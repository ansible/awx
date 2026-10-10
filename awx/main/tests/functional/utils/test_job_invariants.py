from unittest import mock

import pytest

from awx.main.models import HostMetric, Inventory, Job, JobEvent, JobHostSummary
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


def _stats(job, counter, hosts, failures=(), dark=()):
    data = {
        'ok': {h.name: 2 for h in hosts if h.name not in dark},
        'processed': {h.name: 1 for h in hosts},
        'failures': {name: 1 for name in failures},
        'dark': {name: 1 for name in dark},
        'changed': {},
        'skipped': {},
    }
    return _event(job, counter, event='playbook_on_stats', event_data=data)


def _summaries(job, hosts, failures=(), dark=()):
    for h in hosts:
        f, d = int(h.name in failures), int(h.name in dark)
        JobHostSummary.objects.create(job=job, host=h, host_name=h.name, ok=0 if d else 2, processed=1, failures=f, dark=d, failed=bool(f or d))


@pytest.mark.django_db
def test_host_metrics_counted_once(job, hosts):
    _summaries(job, hosts, dark=('h3',))
    snap = {'h1': 4, 'h2': None, 'h3': 7}
    HostMetric.objects.create(hostname='h1', last_automation=job.created, automated_counter=5)
    HostMetric.objects.create(hostname='h2', last_automation=job.created, automated_counter=1)
    HostMetric.objects.create(hostname='h3', last_automation=job.created, automated_counter=7)
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=snap):
        result = job_invariants.check_host_metrics_counted_once(job)
    assert result['ok'], result

    HostMetric.objects.filter(hostname='h1').update(automated_counter=6)
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=snap):
        result = job_invariants.check_host_metrics_counted_once(job)
    assert not result['ok']
    assert result['detail'] == 'h1 +2 (want +1)'


@pytest.mark.django_db
def test_host_metrics_without_snapshot_is_not_checked(job, hosts):
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=None):
        result = job_invariants.check_host_metrics_counted_once(job)
    assert result['ok'] and 'not checked' in result['detail']


@pytest.mark.django_db
def test_host_pointers_consistent(job, hosts, inventory):
    _stats(job, 5, hosts, failures=('h2',))
    _summaries(job, hosts, failures=('h2',))
    inventory.update_computed_fields()
    job.refresh_from_db()
    result = job_invariants.check_host_pointers(job)
    assert result['ok'], result
    assert 'hosts_with_active_failures=1' in result['detail']


@pytest.mark.django_db
def test_host_pointers_flag_stale_inventory_fields_and_summary_mismatch(job, hosts, inventory):
    _stats(job, 5, hosts, failures=('h2',))
    _summaries(job, hosts)  # h2's failure is missing from its summary
    inventory.update_computed_fields()
    job.refresh_from_db()
    result = job_invariants.check_host_pointers(job)
    assert not result['ok']
    assert 'h2 failures=0 != stats 1' in result['detail']

    JobHostSummary.objects.filter(job=job, host_name='h2').update(failures=1, failed=True)
    result = job_invariants.check_host_pointers(job)
    assert not result['ok']
    assert 'inventory hosts_with_active_failures=0 != computed 1' in result['detail']


@pytest.mark.django_db
def test_host_pointers_superseded_and_no_stats(job, hosts, inventory):
    _stats(job, 5, hosts)
    _summaries(job, hosts)
    later = Job.objects.create(inventory=inventory, status='successful')
    _summaries(later, hosts[:1])
    inventory.update_computed_fields()
    job.refresh_from_db()
    result = job_invariants.check_host_pointers(job)
    assert result['ok'], result
    assert 'superseded by later jobs: h1' in result['detail']

    no_stats = Job.objects.create(inventory=inventory, status='failed')
    result = job_invariants.check_host_pointers(no_stats)
    assert result['ok'] and 'no playbook_on_stats; 0 summaries' in result['detail']


def _lines(job, ranges):
    for counter, (start, end) in enumerate(ranges, start=1):
        _event(job, counter, start_line=start, end_line=end, stdout='x\n' * (end - start))


@pytest.mark.django_db
def test_stdout_lines_contiguous(job):
    _lines(job, [(0, 2), (2, 2), (2, 5), (5, 6)])
    result = job_invariants.check_stdout_lines_contiguous(job)
    assert result['ok'], result
    assert 'lines 0-6' in result['detail']


@pytest.mark.django_db
def test_stdout_lines_flag_gaps_and_overlaps(job):
    _lines(job, [(0, 2), (4, 6), (4, 6), (5, 7)])
    result = job_invariants.check_stdout_lines_contiguous(job)
    assert not result['ok']
    assert '1 gaps (lines 2-4 before counter 2)' in result['detail']
    assert '2 overlapping events' in result['detail']


@pytest.mark.django_db
def test_host_ids_constructed_inventory_summaries(organization, inventory, hosts):
    ci = Inventory.objects.create(name='constructed', organization=organization, kind='constructed')
    chosts = [ci.hosts.create(name=h.name, instance_id=str(h.id)) for h in hosts]
    job = Job.objects.create(inventory=ci, status='successful')
    snap = {h.name: h.id for h in chosts}
    for i, (c, h) in enumerate(zip(chosts, hosts), start=1):
        _event(job, i, host=c)
        JobHostSummary.objects.create(job=job, host=h, constructed_host=c, host_name=c.name)
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=snap):
        result = job_invariants.check_host_ids_match_job_start(job)
    assert result['ok'], result

    JobHostSummary.objects.filter(job=job, host_name='h2').update(host=None, constructed_host=hosts[1])
    with mock.patch.object(job_invariants, 'get_snapshot', return_value=snap):
        result = job_invariants.check_host_ids_match_job_start(job)
    assert not result['ok']
    assert f'h2 constructed_host_id {hosts[1].id} != {chosts[1].id}' in result['detail']
    assert f'h2 host_id None != {hosts[1].id}' in result['detail']
