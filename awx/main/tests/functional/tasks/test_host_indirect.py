import yaml
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


def create_event_query(fqcn='demo.query'):
    module_name = f'{fqcn}.example'
    return EventQuery.objects.create(fqcn=fqcn, collection_version='1.0.1', event_query=yaml.dump({module_name: {'query': TEST_JQ}}, default_flow_style=False))


def create_audit_record(name, job, organization, created=now()):
    record = IndirectManagedNodeAudit.objects.create(name=name, job=job, organization=organization)
    record.created = created
    record.save()
    return record


@pytest.fixture
def event_query():
    "This is ordinarily created by the artifacts callback"
    return create_event_query()


@pytest.fixture
def old_audit_record(bare_job, organization):
    created_at = now() - timedelta(days=10)
    return create_audit_record(name="old_job", job=bare_job, organization=organization, created=created_at)


@pytest.fixture
def new_audit_record(bare_job, organization):
    return IndirectManagedNodeAudit.objects.create(name="new_job", job=bare_job, organization=organization)


# ---- end fixtures ----


@pytest.mark.django_db
def test_build_with_no_results(bare_job):
    # never filled in events, should do nothing
    assert build_indirect_host_data(bare_job, {}) == []


@pytest.mark.django_db
def test_collect_an_event(job_with_counted_event):
    records = build_indirect_host_data(job_with_counted_event, {'demo.query.example': {'query': TEST_JQ}})
    assert len(records) == 1


@pytest.mark.django_db
def test_fetch_job_event_query(bare_job, event_query):
    assert fetch_job_event_query(bare_job) == {'demo.query.example': {'query': TEST_JQ}}


@pytest.mark.django_db
def test_fetch_multiple_job_event_query(bare_job):
    create_event_query(fqcn='demo.query')
    create_event_query(fqcn='demo2.query')
    assert fetch_job_event_query(bare_job) == {'demo.query.example': {'query': TEST_JQ}, 'demo2.query.example': {'query': TEST_JQ}}


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
    assert host_audit.name == 'vm-foo'


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
                'demo.query.example': {'query': TEST_JQ},
                'demo.query.example2': {'query': TEST_JQ},
            },
            default_flow_style=False,
        ),
    )

    save_indirect_host_entries(bare_job.id)

    assert IndirectManagedNodeAudit.objects.filter(job=bare_job).count() == 1
    host_audit = IndirectManagedNodeAudit.objects.filter(job=bare_job).first()

    assert host_audit.count == 2
    assert set(host_audit.events) == {'demo.query.example', 'demo.query.example2'}


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
