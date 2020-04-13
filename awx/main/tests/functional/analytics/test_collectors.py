import pytest
import tempfile
import os
import shutil
import csv

from django.utils.timezone import now
from django.db.backends.sqlite3.base import SQLiteCursorWrapper

from awx.main.analytics import collectors

from awx.main.models import (
    ProjectUpdate,
    InventorySource,
)


@pytest.fixture
def sqlite_copy_expert(request):
    # copy_expert is postgres-specific, and SQLite doesn't support it; mock its
    # behavior to test that it writes a file that contains stdout from events
    path = tempfile.mkdtemp(prefix='copied_tables')

    def write_stdout(self, sql, fd):
        # Would be cool if we instead properly disected the SQL query and verified
        # it that way. But instead, we just take the nieve approach here.
        assert sql.startswith('COPY (')
        assert sql.endswith(') TO STDOUT WITH CSV HEADER')

        sql = sql.replace('COPY (', '')
        sql = sql.replace(') TO STDOUT WITH CSV HEADER', '')

        # Remove JSON style queries
        # TODO: could replace JSON style queries with sqlite kind of equivalents
        sql_new = []
        for line in sql.split('\n'):
            if line.find('main_jobevent.event_data::') == -1:
                sql_new.append(line)
        sql = '\n'.join(sql_new)

        self.execute(sql)
        results = self.fetchall()
        headers = [i[0] for i in self.description]

        csv_handle = csv.writer(fd, delimiter=',', quoting=csv.QUOTE_ALL, escapechar='\\', lineterminator='\n')
        csv_handle.writerow(headers)
        csv_handle.writerows(results)


    setattr(SQLiteCursorWrapper, 'copy_expert', write_stdout)
    request.addfinalizer(lambda: shutil.rmtree(path))
    request.addfinalizer(lambda: delattr(SQLiteCursorWrapper, 'copy_expert'))
    return path


@pytest.mark.django_db
def test_copy_tables_unified_job_query(sqlite_copy_expert, project, inventory, job_template):
    '''
    Ensure that various unified job types are in the output of the query.
    '''

    time_start = now()
    inv_src = InventorySource.objects.create(name="inventory_update1", inventory=inventory, source='gce')

    project_update_name = ProjectUpdate.objects.create(project=project, name="project_update1").name
    inventory_update_name = inv_src.create_unified_job().name
    job_name = job_template.create_unified_job().name

    with tempfile.TemporaryDirectory() as tmpdir:
        collectors.copy_tables(time_start, tmpdir)
        with open(os.path.join(tmpdir, 'unified_jobs_table.csv')) as f:
            lines = ''.join([l for l in f])

            assert project_update_name in lines
            assert inventory_update_name in lines
            assert job_name in lines
