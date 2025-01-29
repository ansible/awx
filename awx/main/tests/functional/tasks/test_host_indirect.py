import yaml

import pytest

from awx.main.tasks.host_indirect import build_indirect_host_data, fetch_job_event_query, save_indirect_host_entries
from awx.main.models.event_query import EventQuery
from awx.main.models.indirect_managed_node_audit import IndirectManagedNodeAudit


"""These are unit tests, similar to test_indirect_host_counting in the live tests"""


TEST_JQ = "{canonical_facts: {host_name: .direct_host_name}, facts: {another_host_name: .direct_host_name}}"


@pytest.fixture
def bare_job(job_factory):
    job = job_factory()
    job.installed_collections = {'demo.query.example': {'version': '1.0.1'}}
    job.save(update_fields=['installed_collections'])
    return job


@pytest.fixture
def job_with_counted_event(bare_job):
    bare_job.job_events.create(task='demo.query.example', event_data={'res': {'direct_host_name': 'foo_host'}})
    return bare_job


@pytest.fixture
def event_query():
    "This is ordinarily created by the artifacts callback"
    return EventQuery.objects.create(
        fqcn='demo.query.example', collection_version='1.0.1', event_query=yaml.dump({'demo.query.example': TEST_JQ}, default_flow_style=False)
    )


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
def test_fetch_job_event_query(job_with_counted_event, event_query):
    assert fetch_job_event_query(job_with_counted_event) == {'demo.query.example': TEST_JQ}


@pytest.mark.django_db
def test_save_indirect_host_entries(job_with_counted_event, event_query):
    save_indirect_host_entries(job_with_counted_event.id)
    assert IndirectManagedNodeAudit.objects.filter(job=job_with_counted_event).count() == 1
    host_audit = IndirectManagedNodeAudit.objects.filter(job=job_with_counted_event).first()
    assert host_audit.canonical_facts == {'host_name': 'foo_host'}
    assert host_audit.facts == {'another_host_name': 'foo_host'}
    assert host_audit.organization == job_with_counted_event.organization
