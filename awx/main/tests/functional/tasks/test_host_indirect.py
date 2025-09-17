import yaml
from functools import reduce
from unittest import mock

import pytest

from django.utils.timezone import now, timedelta

from awx.main.tasks.host_indirect import (
    build_indirect_host_data,
    fetch_job_event_query,
    save_indirect_host_entries,
    cleanup_and_save_indirect_host_entries_fallback,
)
from awx.main.models.event_query import EventQuery
from awx.main.models.indirect_managed_node_audit import IndirectManagedNodeAudit

"""These are unit tests, similar to test_indirect_host_counting in the live tests"""


TEST_JQ = "{name: .name, canonical_facts: {host_name: .direct_host_name}, facts: {another_host_name: .direct_host_name}}"


class Query(dict):
    def __init__(self, resolved_action: str, query_jq: dict):
        self._resolved_action = resolved_action.split('.')
        self._collection_ns, self._collection_name, self._module_name = self._resolved_action

        super().__init__({self.resolve_key: {'query': query_jq}})

    def get_fqcn(self):
        return f'{self._collection_ns}.{self._collection_name}'

    @property
    def resolve_value(self):
        return self[self.resolve_key]

    @property
    def resolve_key(self):
        return f'{self.get_fqcn()}.{self._module_name}'

    def resolve(self, module_name=None):
        return {f'{self.get_fqcn()}.{module_name or self._module_name}': self.resolve_value}

    def create_event_query(self, module_name=None):
        if (module_name := module_name or self._module_name) == '*':
            raise ValueError('Invalid module name *')
        return self.create_event_queries([module_name])

    def create_event_queries(self, module_names):
        queries = {}
        for name in module_names:
            queries |= self.resolve(name)
        return EventQuery.objects.create(
            fqcn=self.get_fqcn(),
            collection_version='1.0.1',
            event_query=yaml.dump(queries, default_flow_style=False),
        )

    def create_registered_event(self, job, module_name):
        job.job_events.create(event_data={'resolved_action': f'{self.get_fqcn()}.{module_name}', 'res': {'direct_host_name': 'foo_host', 'name': 'vm-foo'}})


@pytest.fixture
def bare_job(job_factory):
    job = job_factory()
    job.installed_collections = {'demo.query': {'version': '1.0.1'}, 'demo2.query': {'version': '1.0.1'}}
    job.event_queries_processed = False
    job.save(update_fields=['installed_collections', 'event_queries_processed'])
    return job


def create_registered_event(job, task_name='demo.query.example'):
    return job.job_events.create(event_data={'resolved_action': task_name, 'res': {'direct_host_name': 'foo_host', 'name': 'vm-foo'}})


@pytest.fixture
def job_with_counted_event(bare_job):
    create_registered_event(bare_job)
    return bare_job


def create_audit_record(name, job, organization, created=now()):
    record = IndirectManagedNodeAudit.objects.create(name=name, job=job, organization=organization)
    record.created = created
    record.save()
    return record


@pytest.fixture
def event_query():
    "This is ordinarily created by the artifacts callback"
    return Query('demo.query.example', TEST_JQ).create_event_query()


@pytest.fixture
def old_audit_record(bare_job, organization):
    created_at = now() - timedelta(days=10)
    return create_audit_record(name="old_job", job=bare_job, organization=organization, created=created_at)


@pytest.fixture
def new_audit_record(bare_job, organization):
    return IndirectManagedNodeAudit.objects.create(name="new_job", job=bare_job, organization=organization)


# ---- end fixtures ----


@pytest.mark.django_db
@pytest.mark.parametrize(
    'queries,expected_matches',
    (
        pytest.param(
            [],
            0,
            id='no_results',
        ),
        pytest.param(
            [Query('demo.query.example', TEST_JQ)],
            1,
            id='fully_qualified',
        ),
        pytest.param(
            [Query('demo.query.*', TEST_JQ)],
            1,
            id='wildcard',
        ),
        pytest.param(
            [
                Query('demo.query.*', TEST_JQ),
                Query('demo.query.example', TEST_JQ),
            ],
            1,
            id='wildcard_and_fully_qualified',
        ),
        pytest.param(
            [
                Query('demo.query.*', TEST_JQ),
                Query('demo.query.example', {}),
            ],
            0,
            id='wildcard_and_fully_qualified',
        ),
        pytest.param(
            [
                Query('demo.query.example', {}),
                Query('demo.query.*', TEST_JQ),
            ],
            0,
            id='ordering_should_not_matter',
        ),
    ),
)
def test_build_indirect_host_data(job_with_counted_event, queries: Query, expected_matches: int):
    data = build_indirect_host_data(job_with_counted_event, {k: v for d in queries for k, v in d.items()})
    assert len(data) == expected_matches


@mock.patch('awx.main.tasks.host_indirect.logger.debug')
@pytest.mark.django_db
@pytest.mark.parametrize(
    'task_name',
    (
        pytest.param(
            'demo.query',
            id='no_results',
        ),
        pytest.param(
            'demo',
            id='no_results',
        ),
        pytest.param(
            'a.b.c.d',
            id='no_results',
        ),
    ),
)
def test_build_indirect_host_data_malformed_module_name(mock_logger_debug, bare_job, task_name: str):
    create_registered_event(bare_job, task_name)
    assert build_indirect_host_data(bare_job, Query('demo.query.example', TEST_JQ)) == []
    mock_logger_debug.assert_called_once_with(f"Malformed invocation module name '{task_name}'. Expected to be of the form 'a.b.c'")


@mock.patch('awx.main.tasks.host_indirect.logger.info')
@pytest.mark.django_db
@pytest.mark.parametrize(
    'query',
    (
        pytest.param(
            'demo.query',
            id='no_results',
        ),
        pytest.param(
            'demo',
            id='no_results',
        ),
        pytest.param(
            'a.b.c.d',
            id='no_results',
        ),
    ),
)
def test_build_indirect_host_data_malformed_query(mock_logger_info, job_with_counted_event, query: str):
    assert build_indirect_host_data(job_with_counted_event, {query: {'query': TEST_JQ}}) == []
    mock_logger_info.assert_called_once_with(f"Skiping malformed query '{query}'. Expected to be of the form 'a.b.c'")


@pytest.mark.django_db
@pytest.mark.parametrize(
    'query',
    (
        pytest.param(
            Query('demo.query.example', TEST_JQ),
            id='fully_qualified',
        ),
        pytest.param(
            Query('demo.query.*', TEST_JQ),
            id='wildcard',
        ),
    ),
)
def test_fetch_job_event_query(bare_job, query: Query):
    query.create_event_query(module_name='example')
    assert fetch_job_event_query(bare_job) == query.resolve('example')


@pytest.mark.django_db
@pytest.mark.parametrize(
    'queries',
    (
        [
            Query('demo.query.example', TEST_JQ),
            Query('demo2.query.example', TEST_JQ),
        ],
        [
            Query('demo.query.*', TEST_JQ),
            Query('demo2.query.example', TEST_JQ),
        ],
    ),
)
def test_fetch_multiple_job_event_query(bare_job, queries: list[Query]):
    for q in queries:
        q.create_event_query(module_name='example')
    assert fetch_job_event_query(bare_job) == reduce(lambda acc, q: acc | q.resolve('example'), queries, {})


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('state',),
    (
        pytest.param(
            [
                (
                    Query('demo.query.example', TEST_JQ),
                    ['example'],
                ),
            ],
            id='fully_qualified',
        ),
        pytest.param(
            [
                (
                    Query('demo.query.example', TEST_JQ),
                    ['example'] * 3,
                ),
            ],
            id='multiple_events_same_module_same_host',
        ),
        pytest.param(
            [
                (
                    Query('demo.query.example', TEST_JQ),
                    ['example'],
                ),
                (
                    Query('demo2.query.example', TEST_JQ),
                    ['example'],
                ),
            ],
            id='multiple_modules',
        ),
        pytest.param(
            [
                (
                    Query('demo.query.*', TEST_JQ),
                    ['example', 'example2'],
                ),
            ],
            id='multiple_modules_same_collection',
        ),
    ),
)
def test_save_indirect_host_entries(bare_job, state):
    all_task_names = []
    for entry in state:
        query, module_names = entry
        all_task_names.extend([f'{query.get_fqcn()}.{module_name}' for module_name in module_names])
        query.create_event_queries(module_names)
        [query.create_registered_event(bare_job, n) for n in module_names]

    save_indirect_host_entries(bare_job.id)
    bare_job.refresh_from_db()

    assert bare_job.event_queries_processed is True

    assert IndirectManagedNodeAudit.objects.filter(job=bare_job).count() == 1
    host_audit = IndirectManagedNodeAudit.objects.filter(job=bare_job).first()

    assert host_audit.count == len(all_task_names)
    assert host_audit.canonical_facts == {'host_name': 'foo_host'}
    assert host_audit.facts == {'another_host_name': 'foo_host'}
    assert host_audit.organization == bare_job.organization
    assert host_audit.name == 'vm-foo'
    assert set(host_audit.events) == set(all_task_names)


@pytest.mark.django_db
def test_events_not_fully_processed_no_op(bare_job):
    # I have a job that produced 12 events, but those are not saved
    bare_job.emitted_events = 12
    bare_job.finished = now()
    bare_job.save(update_fields=['emitted_events', 'finished'])

    # Running the normal post-run task will do nothing at this point
    assert bare_job.event_queries_processed is False
    with mock.patch('time.sleep'):  # for test speedup
        save_indirect_host_entries(bare_job.id)
    bare_job.refresh_from_db()
    assert bare_job.event_queries_processed is False

    # Right away, the fallback processing will not run either
    cleanup_and_save_indirect_host_entries_fallback()
    bare_job.refresh_from_db()
    assert bare_job.event_queries_processed is False

    # After 3 hours have passed...
    bare_job.finished = now() - timedelta(hours=3)

    # Create the expected job events
    for _ in range(12):
        create_registered_event(bare_job)

    bare_job.save(update_fields=['finished'])

    # The fallback task will now process indirect host query data for this job
    cleanup_and_save_indirect_host_entries_fallback()

    # Test code to process anyway, events collected or not
    save_indirect_host_entries(bare_job.id, wait_for_events=False)
    bare_job.refresh_from_db()
    assert bare_job.event_queries_processed is True


@pytest.mark.django_db
def test_job_id_does_not_exist():
    save_indirect_host_entries(10000001)


@pytest.mark.django_db
def test_cleanup_old_audit_records(old_audit_record, new_audit_record):
    count_before_cleanup = IndirectManagedNodeAudit.objects.count()
    assert count_before_cleanup == 2
    cleanup_and_save_indirect_host_entries_fallback()
    count_after_cleanup = IndirectManagedNodeAudit.objects.count()
    assert count_after_cleanup == 1
