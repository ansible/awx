import pytest
import tempfile
import os
import re
import csv
from io import StringIO

from django.utils.timezone import now
from datetime import timedelta
from django.db.backends.sqlite3.base import SQLiteCursorWrapper

from awx.main.analytics import collectors

from awx.main.models import (
    ProjectUpdate,
    InventorySource,
    WorkflowJob,
    WorkflowJobNode,
    JobTemplate,
)


class MockCopy:
    headers = None
    results = None
    sent_data = False

    def __init__(self, sql, parent_connection):
        # Would be cool if we instead properly disected the SQL query and verified
        # it that way. But instead, we just take the naive approach here.
        self.results = None
        self.headers = None
        sql = sql.strip()
        assert sql.startswith("COPY (")
        assert sql.endswith(") TO STDOUT WITH CSV HEADER")

        sql = sql.replace("COPY (", "")
        sql = sql.replace(") TO STDOUT WITH CSV HEADER", "")
        # sqlite equivalent
        sql = sql.replace("ARRAY_AGG", "GROUP_CONCAT")
        # SQLite doesn't support isoformatted dates, because that would be useful
        sql = sql.replace("+00:00", "")
        i = re.compile(r'(?P<date>\d\d\d\d-\d\d-\d\d)T')
        sql = i.sub(r'\g<date> ', sql)

        # Remove JSON style queries
        # TODO: could replace JSON style queries with sqlite kind of equivalents
        sql_new = []
        for line in sql.split("\n"):
            if line.find("main_jobevent.event_data::") == -1:
                sql_new.append(line)
            elif not line.endswith(","):
                sql_new[-1] = sql_new[-1].rstrip(",")
        sql = "\n".join(sql_new)
        parent_connection.execute(sql)
        self.results = parent_connection.fetchall()
        self.headers = [i[0] for i in parent_connection.description]

    def read(self):
        if not self.sent_data:
            mem_file = StringIO()
            csv_handle = csv.writer(
                mem_file,
                delimiter=",",
                quoting=csv.QUOTE_ALL,
                escapechar="\\",
                lineterminator="\n",
            )
            if self.headers:
                csv_handle.writerow(self.headers)
            if self.results:
                csv_handle.writerows(self.results)
            self.sent_data = True
            return memoryview((mem_file.getvalue()).encode())
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def sqlite_copy(request, mocker):
    # copy is postgres-specific, and SQLite doesn't support it; mock its
    # behavior to test that it writes a file that contains stdout from events

    def write_stdout(self, sql):
        mock_copy = MockCopy(sql, self)
        return mock_copy

    mocker.patch.object(SQLiteCursorWrapper, 'copy', write_stdout, create=True)


@pytest.mark.django_db
def test_copy_tables_unified_job_query(sqlite_copy, project, inventory, job_template):
    """
    Ensure that various unified job types are in the output of the query.
    """

    time_start = now() - timedelta(hours=9)
    inv_src = InventorySource.objects.create(name="inventory_update1", inventory=inventory, source="gce")

    project_update_name = ProjectUpdate.objects.create(project=project, name="project_update1").name
    inventory_update_name = inv_src.create_unified_job().name
    job_name = job_template.create_unified_job().name

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.unified_jobs_table(time_start, tmpdir, until=now() + timedelta(seconds=1))
        with open(os.path.join(tmpdir, "unified_jobs_table.csv")) as f:
            lines = "".join([line for line in f])

            assert project_update_name in lines
            assert inventory_update_name in lines
            assert job_name in lines


@pytest.fixture
def workflow_job(states=["new", "new", "new", "new", "new"]):
    """
    Workflow topology:
           node[0]
            /\
          s/  \f
          /    \
    node[1,5] node[3]
         /       \
       s/         \f
       /           \
    node[2]       node[4]
    """
    wfj = WorkflowJob.objects.create()
    jt = JobTemplate.objects.create(name="test-jt")
    nodes = [WorkflowJobNode.objects.create(workflow_job=wfj, unified_job_template=jt) for i in range(0, 6)]
    for node, state in zip(nodes, states):
        if state:
            node.job = jt.create_job()
            node.job.status = state
            node.job.save()
            node.save()
    nodes[0].success_nodes.add(nodes[1])
    nodes[0].success_nodes.add(nodes[5])
    nodes[1].success_nodes.add(nodes[2])
    nodes[0].failure_nodes.add(nodes[3])
    nodes[3].failure_nodes.add(nodes[4])
    return wfj


@pytest.mark.django_db
def test_copy_tables_workflow_job_node_query(sqlite_copy, workflow_job):
    time_start = now() - timedelta(hours=9)

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.workflow_job_node_table(time_start, tmpdir, until=now() + timedelta(seconds=1))
        with open(os.path.join(tmpdir, "workflow_job_node_table.csv")) as f:
            reader = csv.reader(f)
            # Pop the headers
            next(reader)
            lines = [line for line in reader]

            ids = [int(line[0]) for line in lines]

            assert ids == list(workflow_job.workflow_nodes.all().values_list("id", flat=True))

            for index, relationship in zip([7, 8, 9], ["success_nodes", "failure_nodes", "always_nodes"]):
                for i, l in enumerate(lines):
                    related_nodes = [int(e) for e in l[index].split(",")] if l[index] else []
                    assert related_nodes == list(
                        getattr(workflow_job.workflow_nodes.all()[i], relationship).all().values_list("id", flat=True)
                    ), f"(right side) workflow_nodes.all()[{i}].{relationship}.all()"
