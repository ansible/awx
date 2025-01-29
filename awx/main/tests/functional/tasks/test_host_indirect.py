import yaml

import pytest

from awx.main.tasks.host_indirect import build_indirect_host_data, fetch_job_event_query, save_indirect_host_entries, get_hashable_form
from awx.main.models.event_query import EventQuery
from awx.main.models.indirect_managed_node_audit import IndirectManagedNodeAudit


"""These are unit tests, similar to test_indirect_host_counting in the live tests"""


TEST_JQ = "{canonical_facts: {host_name: .direct_host_name}, facts: {another_host_name: .direct_host_name}}"


@pytest.fixture
def bare_job(job_factory):
    job = job_factory()
    job.installed_collections = {'demo.query': {'version': '1.0.1'}, 'demo2.query': {'version': '1.0.1'}}
    job.save(update_fields=['installed_collections'])
    return job


def create_registered_event(job, task_name='demo.query.example'):
    return job.job_events.create(task=task_name, event_data={'res': {'direct_host_name': 'foo_host'}})


@pytest.fixture
def job_with_counted_event(bare_job):
    create_registered_event(bare_job)
    return bare_job


def create_event_query(fqcn='demo.query'):
    module_name = f'{fqcn}.example'
    return EventQuery.objects.create(fqcn=fqcn, collection_version='1.0.1', event_query=yaml.dump({module_name: TEST_JQ}, default_flow_style=False))


@pytest.fixture
def event_query():
    "This is ordinarily created by the artifacts callback"
    return create_event_query()


# ---- end fixtures ----


@pytest.mark.django_db
def test_build_with_no_results(job_factory):
    # never filled in events, should do nothing
    job = job_factory()
    assert job.event_queries_processed is False
    assert build_indirect_host_data(job, {}) == []


@pytest.mark.django_db
def test_collect_an_event(job_with_counted_event):
    records = build_indirect_host_data(job_with_counted_event, {'demo.query.example': TEST_JQ})
    assert len(records) == 1


@pytest.mark.django_db
def test_fetch_job_event_query(bare_job, event_query):
    assert fetch_job_event_query(bare_job) == {'demo.query.example': TEST_JQ}


@pytest.mark.django_db
def test_fetch_multiple_job_event_query(bare_job):
    create_event_query(fqcn='demo.query')
    create_event_query(fqcn='demo2.query')
    assert fetch_job_event_query(bare_job) == {'demo.query.example': TEST_JQ, 'demo2.query.example': TEST_JQ}


@pytest.mark.django_db
def test_save_indirect_host_entries(job_with_counted_event, event_query):
    assert job_with_counted_event.event_queries_processed is False
    save_indirect_host_entries(job_with_counted_event.id)
    job_with_counted_event.refresh_from_db()
    assert job_with_counted_event.event_queries_processed is True
    assert IndirectManagedNodeAudit.objects.filter(job=job_with_counted_event).count() == 1
    host_audit = IndirectManagedNodeAudit.objects.filter(job=job_with_counted_event).first()
    assert host_audit.count == 1
    assert host_audit.canonical_facts == {'host_name': 'foo_host'}
    assert host_audit.facts == {'another_host_name': 'foo_host'}
    assert host_audit.organization == job_with_counted_event.organization


@pytest.mark.django_db
def test_multiple_events_same_module_same_host(bare_job, event_query):
    "This tests that the count field gives correct answers"
    create_registered_event(bare_job)
    create_registered_event(bare_job)
    create_registered_event(bare_job)

    save_indirect_host_entries(bare_job.id)

    assert IndirectManagedNodeAudit.objects.filter(job=bare_job).count() == 1
    host_audit = IndirectManagedNodeAudit.objects.filter(job=bare_job).first()

    assert host_audit.count == 3
    assert host_audit.events == ['demo.query.example']


@pytest.mark.django_db
def test_multiple_registered_modules(bare_job):
    "This tests that the events will list multiple modules if more than 1 module from different collections is registered and used"
    create_registered_event(bare_job, task_name='demo.query.example')
    create_registered_event(bare_job, task_name='demo2.query.example')

    # These take the place of using the event_query fixture
    create_event_query(fqcn='demo.query')
    create_event_query(fqcn='demo2.query')

    save_indirect_host_entries(bare_job.id)

    assert IndirectManagedNodeAudit.objects.filter(job=bare_job).count() == 1
    host_audit = IndirectManagedNodeAudit.objects.filter(job=bare_job).first()

    assert host_audit.count == 2
    assert set(host_audit.events) == {'demo.query.example', 'demo2.query.example'}


@pytest.mark.django_db
def test_multiple_registered_modules_same_collection(bare_job):
    "This tests that the events will list multiple modules if more than 1 module in same collection is registered and used"
    create_registered_event(bare_job, task_name='demo.query.example')
    create_registered_event(bare_job, task_name='demo.query.example2')

    # Takes place of event_query fixture, doing manually here
    EventQuery.objects.create(
        fqcn='demo.query',
        collection_version='1.0.1',
        event_query=yaml.dump(
            {
                'demo.query.example': TEST_JQ,
                'demo.query.example2': TEST_JQ,
            },
            default_flow_style=False,
        ),
    )

    save_indirect_host_entries(bare_job.id)

    assert IndirectManagedNodeAudit.objects.filter(job=bare_job).count() == 1
    host_audit = IndirectManagedNodeAudit.objects.filter(job=bare_job).first()

    assert host_audit.count == 2
    assert set(host_audit.events) == {'demo.query.example', 'demo.query.example2'}


class TestHashableForm:
    def test_same_dict(self):
        assert get_hashable_form({'a': 'b'}) == get_hashable_form({'a': 'b'})

    def test_same_list(self):
        assert get_hashable_form(['a', 'b']) == get_hashable_form(['a', 'b'])
        assert get_hashable_form(('a', 'b')) == get_hashable_form(('a', 'b'))

    def test_different_list(self):
        assert get_hashable_form(['a', 'b']) != get_hashable_form(['a', 'c'])
        assert get_hashable_form(('a', 'b')) != get_hashable_form(('a', 'c'))

    def test_values_different(self):
        assert get_hashable_form({'a': 'b'}) != get_hashable_form({'a': 'c'})

    def test_has_extra_key(self):
        assert get_hashable_form({'a': 'b'}) != get_hashable_form({'a': 'b', 'c': 'd'})

    def test_nested_dictionaries_different(self):
        assert get_hashable_form({'a': {'b': 'c'}}) != get_hashable_form({'a': {'b': 'd'}})

    def test_nested_dictionaries_same(self):
        assert get_hashable_form({'a': {'b': 'c'}}) == get_hashable_form({'a': {'b': 'c'}})

    def test_nested_lists_different(self):
        assert get_hashable_form({'a': ['b', 'c']}) != get_hashable_form({'a': ['b', 'd']})
        assert get_hashable_form({'a': ('b', 'c')}) != get_hashable_form({'a': ('b', 'd')})

    def test_nested_lists_same(self):
        assert get_hashable_form({'a': ['b', 'c']}) == get_hashable_form({'a': ['b', 'c']})
        assert get_hashable_form({'a': ('b', 'c')}) == get_hashable_form({'a': ('b', 'c')})
        assert hash(get_hashable_form({'a': ['b', 'c']})) == hash(get_hashable_form({'a': ['b', 'c']}))

    def test_list_nested_lists_different(self):
        assert get_hashable_form(['a', ['b', 'c']]) != get_hashable_form(['a', ['b', 'd']])
        assert get_hashable_form(['a', ('b', 'c')]) != get_hashable_form(['a', ('b', 'd')])

    def test_list_nested_lists_same(self):
        assert get_hashable_form(['a', ['b', 'c']]) == get_hashable_form(['a', ['b', 'c']])
        assert get_hashable_form(['a', ('b', 'c')]) == get_hashable_form(['a', ('b', 'c')])
        assert hash(get_hashable_form(['a', ('b', 'c')])) == hash(get_hashable_form(['a', ('b', 'c')]))

    def test_list_nested_dicts_different(self):
        assert get_hashable_form(['a', {'b': 'c'}]) != get_hashable_form(['a', {'b': 'd'}])
        assert hash(get_hashable_form(['a', {'b': 'c'}])) != hash(get_hashable_form(['a', {'b': 'd'}]))

    def test_list_nested_dicts_same(self):
        assert get_hashable_form(['a', {'b': 'c'}]) == get_hashable_form(['a', {'b': 'c'}])
        assert hash(get_hashable_form(['a', {'b': 'c'}])) == hash(get_hashable_form(['a', {'b': 'c'}]))
