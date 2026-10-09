from unittest import mock

import pytest

from awx.main.models import Job, JobEvent, JobHostSummary
from awx.main.utils import job_invariants


def _event(job, counter, event='runner_on_ok', host=None, **kw):
    return JobEvent.objects.create(
        job=job,
        counter=counter,
        event=event,
        job_created=job.created,
        host_name=host.name if host else '',
        host_id=host.id if host else None,
        **kw,
    )


@pytest.fixture
def hosts(inventory):
    return [inventory.hosts.create(name=f'h{i}') for i in range(1, 4)]


@pytest.fixture
def job(inventory):
    return Job.objects.create(inventory=inventory, status='successful')


def _snapshot(hosts):
    return {h.name: h.id for h in hosts}


@pytest.mark.django_db
def test_host_ids_match_when_events_and_summaries_use_job_start_ids(job, hosts):
    for i, h in enumerate(hosts, start=1):
        _event(job, i, host=h)
        JobHostSummary.objects.create(job=job, host=h, host_name=h.name)
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=_snapshot(hosts)):
        result = job_invariants.check_host_ids_match_job_start(job)
    assert result['ok'], result


@pytest.mark.django_db
def test_host_ids_flag_replayed_events_with_rebuilt_map(job, hosts, inventory):
    """The host-map drift seen in adoption: a recreated host gets the new id, a deleted one None."""
    snap = _snapshot(hosts)
    h1, h2, h3 = hosts
    _event(job, 1, host=h1)
    _event(job, 2, host=h2)
    h2.delete()
    JobEvent.objects.create(job=job, counter=3, event='runner_on_ok', job_created=job.created, host_name='h2', host_id=None)
    h3_old = h3.id
    h3.delete()
    h3_new = inventory.hosts.create(name='h3')
    _event(job, 4, host=h3_new)
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=snap):
        result = job_invariants.check_host_ids_match_job_start(job)
    assert not result['ok']
    assert 'h2' in result['detail'] and f'h3 [{h3_new.id}] != {h3_old}' in result['detail']


@pytest.mark.django_db
def test_host_summaries_expect_none_for_deleted_hosts(job, hosts, inventory):
    snap = _snapshot(hosts)
    h1, h2, _ = hosts
    h2.delete()
    replacement = inventory.hosts.create(name='h2')
    JobHostSummary.objects.create(job=job, host=h1, host_name='h1')
    JobHostSummary.objects.create(job=job, host=replacement, host_name='h2')
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=snap):
        result = job_invariants.check_host_ids_match_job_start(job)
    assert not result['ok']
    assert f'summaries: h2 {replacement.id} != None' in result['detail']

    JobHostSummary.objects.filter(job=job, host_name='h2').update(host=None)
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=snap):
        assert job_invariants.check_host_ids_match_job_start(job)['ok']


@pytest.mark.django_db
def test_host_ids_without_snapshot_checks_consistency(job, hosts, inventory):
    h1 = hosts[0]
    _event(job, 1, host=h1)
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=None):
        result = job_invariants.check_host_ids_match_job_start(job)
    assert result['ok'] and 'consistency only' in result['detail']

    JobEvent.objects.create(job=job, counter=2, event='runner_on_ok', job_created=job.created, host_name='h1', host_id=None)
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=None):
        result = job_invariants.check_host_ids_match_job_start(job)
    assert not result['ok'] and 'h1' in result['detail']


@pytest.mark.django_db
def test_playbook_events_complete(job):
    for i in range(1, 6):
        _event(job, i)
    _event(job, 6, event='playbook_on_stats')
    _event(job, 7, event='verbose')
    result = job_invariants.check_playbook_events_complete(job)
    assert result['ok'], result
    assert '6 of 6 stored' in result['detail']


@pytest.mark.django_db
def test_playbook_events_complete_flags_holes_before_final_event(job):
    """A harvest that lost the middle of the stream but kept the tail."""
    for i in (1, 2, 3, 9, 10):
        _event(job, i)
    _event(job, 11, event='playbook_on_stats')
    result = job_invariants.check_playbook_events_complete(job)
    assert not result['ok']
    assert '6 of 11 stored, 5 missing' in result['detail']


@pytest.mark.django_db
@pytest.mark.parametrize(
    'status, cancel_flag, ok',
    [('successful', False, False), ('failed', False, False), ('error', False, True), ('canceled', False, True), ('failed', True, True)],
)
def test_playbook_events_complete_without_final_event(job, status, cancel_flag, ok):
    """Output cut short with no gap: nothing after the cut was ever stored."""
    Job.objects.filter(pk=job.pk).update(status=status, cancel_flag=cancel_flag)
    job.refresh_from_db()
    for i in range(1, 17):
        _event(job, i)
    result = job_invariants.check_playbook_events_complete(job)
    assert result['ok'] is ok
    assert 'no playbook_on_stats event; 16 events stored' in result['detail']


@pytest.mark.django_db
def test_playbook_events_complete_counts_duplicates_once(job):
    for i in (1, 2, 2, 3, 3):
        _event(job, i)
    _event(job, 4, event='playbook_on_stats')
    result = job_invariants.check_playbook_events_complete(job)
    assert result['ok'], result
    assert '4 of 4 stored' in result['detail']
