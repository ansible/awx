"""Adoption of orphaned jobs: the heartbeat hands a running job its dispatcher no longer tracks to
adopt_job, which reattaches to the job's receptor work unit, replays its events and finalizes it.

Tests that use FakeReceptorWork drive the real reattach, streaming, dedup and finalize code. Only
receptor and the callback-receiver queue (RecordingDispatcher) are replaced.

Tests marked xfail reproduce a defect found on devel and assert the behavior it should have.
Each names its Jira bug; when the bug is fixed the test passes, strict xfail fails the run, and
the marker comes off.

``TIMEOUT`` is HADR_JOB_ADOPTION_TIMEOUT.
"""

import json
import os
from unittest import mock

import pytest
from django.db import DatabaseError
from django.utils.timezone import now, timedelta

from awx.main.models import Inventory, Job, JobEvent
from awx.main.tasks import jobs
from awx.main.tasks.receptor import reattach_to_work_unit
from awx.main.tasks.system import (
    adopt_job,
    awx_receptor_workunit_reaper,
)
from awx.main.tests.adoption_cluster import UNIT, adoption_env, running_job, running_unit, save_dispatched_events, stats_event
from awx.main.tests.fake_clock import FakeClock
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events

TIMEOUT = 300


@pytest.fixture(autouse=True)
def fake_receptor_env(settings, tmp_path):
    """Everything adoption touches outside the database, patched; see adoption_env."""
    settings.HADR_JOB_ADOPTION_TIMEOUT = TIMEOUT
    with adoption_env(settings, tmp_path):
        yield


@pytest.fixture
def job_with_unit(me_inst):
    return Job.objects.create(controller_node=me_inst.hostname, execution_node='receptor-1', status='running', work_unit_id=UNIT)


def save_events(job, counters, created=None):
    for counter in counters:
        JobEvent.objects.create(job=job, counter=counter, event='runner_on_ok', job_created=job.created)
    if created:
        JobEvent.objects.filter(job=job).update(created=created)


@pytest.mark.django_db
def test_finished_unit_is_replayed_and_finalized(job_with_unit):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(30))})

    assert reattach_to_work_unit(job_with_unit, work) is True

    job_with_unit.refresh_from_db()
    assert job_with_unit.status == 'successful'
    assert RecordingDispatcher.counters() == list(range(1, 31))
    assert UNIT not in work.units, 'work unit released after finalize'


@pytest.mark.django_db
@pytest.mark.parametrize(
    'saved, unit_events, expected',
    [
        pytest.param(list(range(1, 21)), 30, list(range(21, 31)), id='saved-in-order'),
        pytest.param([*range(1, 11), 13], 20, [11, 12, *range(14, 21)], id='saved-out-of-order'),
    ],
)
def test_events_already_saved_are_not_dispatched_again(job_with_unit, saved, unit_events, expected):
    """``saved-out-of-order``: Parallel callback workers can commit counter 13 before 11 and 12."""
    save_events(job_with_unit, saved)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(unit_events))})

    reattach_to_work_unit(job_with_unit, work)

    assert RecordingDispatcher.counters() == expected


@pytest.mark.django_db
def test_failed_playbook_finalizes_failed(job_with_unit):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10, failed_tasks=[5]), status='failed', exit_code=2)})

    reattach_to_work_unit(job_with_unit, work)

    job_with_unit.refresh_from_db()
    assert job_with_unit.status == 'failed'


@pytest.mark.django_db
def test_unit_still_running_is_deferred(job_with_unit):
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), state='Running')})

    assert reattach_to_work_unit(job_with_unit, work) is False

    job_with_unit.refresh_from_db()
    assert job_with_unit.status == 'running'
    assert RecordingDispatcher.dispatched == []
    assert UNIT in work.units


@pytest.mark.django_db
def test_unit_gone_is_deferred(job_with_unit):
    """The unit was released, or the node lost it, before adoption."""
    work = FakeReceptorWork()

    assert reattach_to_work_unit(job_with_unit, work) is False

    job_with_unit.refresh_from_db()
    assert job_with_unit.status == 'running'


@pytest.mark.django_db
def test_stream_broken_mid_replay_fails_a_successful_unit(job_with_unit):
    """The unit succeeded, but the results stream ends after 12 of 30 events. Today the job is finalized
    failed, with only the events read before the break.
    """
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(30), break_after=12)})

    reattach_to_work_unit(job_with_unit, work)

    job_with_unit.refresh_from_db()
    assert job_with_unit.status == 'failed'
    assert RecordingDispatcher.counters() == list(range(1, 13))
    assert 'Unexpected empty line' in job_with_unit.job_explanation


@pytest.mark.django_db
def test_workunit_reaper_releases_units_of_finished_jobs(me_inst, settings):
    settings.RECEPTOR_RELEASE_WORK = True
    finished = Job.objects.create(controller_node=me_inst.hostname, status='successful', work_unit_id='done')
    running = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='live')
    work = FakeReceptorWork({'done': FakeWorkUnit(), 'live': FakeWorkUnit(state='Running')})

    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl'),
        mock.patch('awx.main.tasks.system.ReceptorWork', return_value=work),
        mock.patch('awx.main.tasks.system.administrative_workunit_reaper'),
    ):
        awx_receptor_workunit_reaper()

    assert ('cancel', finished.work_unit_id) in work.calls
    assert finished.work_unit_id not in work.units
    assert running.work_unit_id in work.units


@pytest.fixture
def quiet_orphan(me_inst):
    """A running job whose last saved event was written at the returned time."""
    started = now() - timedelta(hours=1)
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, started=started)
    JobEvent.objects.create(job=job, counter=1, event='playbook_on_start', job_created=job.created)
    last_event = now() - timedelta(minutes=10)
    JobEvent.objects.filter(job=job).update(created=last_event)
    return job, last_event


@pytest.mark.django_db
def test_orphan_within_the_deadline_is_adopted(quiet_orphan):
    job, last_event = quiet_orphan
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})
    clock = FakeClock(last_event + timedelta(seconds=TIMEOUT - 1))

    adopt_job(job.id, open_work=lambda: work, clock=clock)

    job.refresh_from_db()
    assert job.status == 'successful'
    assert job.finished == clock()
    assert RecordingDispatcher.counters() == list(range(2, 11))
    assert ('close',) in work.calls


@pytest.mark.django_db
def test_orphan_past_the_deadline_is_failed_without_contacting_receptor(quiet_orphan):
    job, last_event = quiet_orphan
    opened = mock.Mock()

    adopt_job(job.id, open_work=opened, clock=FakeClock(last_event + timedelta(seconds=TIMEOUT + 1)))

    job.refresh_from_db()
    assert job.status == 'failed'
    assert 'HADR_JOB_ADOPTION_TIMEOUT' in job.job_explanation
    opened.assert_not_called()


@pytest.fixture
def orphan(me_inst):
    """A running job this controller lost track of, started a minute ago."""
    return Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, started=now() - timedelta(seconds=60))


@pytest.mark.xfail(strict=True, reason='AAP-96828: an error while finalizing a resumed job releases its unit and strands the job')
@pytest.mark.django_db
def test_finalize_error_is_retried_on_the_next_adoption(orphan):
    """Finalize strand. The first adoption streams the whole unit, then finalization raises. Today the
    unit is released anyway, so the next adoption finds nothing and the job stays running until the
    adoption timeout fails it.
    """
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})
    real_finalize = jobs._finalize_job_run
    attempts = []

    def finalize_fails_once(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise DatabaseError('connection lost during finalize')
        return real_finalize(*args, **kwargs)

    with mock.patch('awx.main.tasks.jobs._finalize_job_run', side_effect=finalize_fails_once):
        adopt_job(orphan.id, open_work=lambda: work)
        adopt_job(orphan.id, open_work=lambda: work)

    orphan.refresh_from_db()
    assert orphan.status == 'successful'


@pytest.mark.xfail(strict=True, reason='AAP-96829: a restart fails a healthy job with a long quiet task while its playbook keeps running')
@pytest.mark.django_db
def test_quiet_job_whose_unit_is_still_running_is_not_failed(orphan):
    """Quiet deadline. The playbook is in a long task with no output, so its last event is older than
    HADR_JOB_ADOPTION_TIMEOUT, but receptor reports the unit running. Today adoption measures the
    deadline from the last event and fails the job, while the playbook keeps running on the execution
    node.
    """
    clock = FakeClock()
    save_events(orphan, range(1, 6), created=clock() - timedelta(seconds=TIMEOUT + 60))
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), state='Running')})

    adopt_job(orphan.id, open_work=lambda: work, clock=clock)

    orphan.refresh_from_db()
    assert orphan.status == 'running'


@pytest.mark.django_db
def test_adoption_waits_through_repeated_restarts_and_replays_each_event_once(orphan):
    """Three restarts during one job. While the unit runs, each adoption defers; once it finishes, the
    replay sends only the events not yet saved, each once.
    """
    clock = FakeClock()
    save_events(orphan, range(1, 13), created=clock())
    unit = FakeWorkUnit(make_events(30), state='Running')
    work = FakeReceptorWork({UNIT: unit})

    for _ in range(3):
        adopt_job(orphan.id, open_work=lambda: work, clock=clock)
        orphan.refresh_from_db()
        assert orphan.status == 'running'
        assert RecordingDispatcher.dispatched == []
        clock.advance(60)

    unit.state = 'Succeeded'
    adopt_job(orphan.id, open_work=lambda: work, clock=clock)

    orphan.refresh_from_db()
    assert orphan.status == 'successful'
    assert RecordingDispatcher.counters() == list(range(13, 31))


@pytest.mark.django_db
def test_large_replay_sends_every_event_once(orphan):
    """Large replay. A 20,000 event unit with the first 500 already saved."""
    save_events(orphan, range(1, 501))
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(20000))})

    adopt_job(orphan.id, open_work=lambda: work)

    orphan.refresh_from_db()
    assert orphan.status == 'successful'
    assert RecordingDispatcher.counters() == list(range(501, 20001))


@pytest.mark.django_db
def test_unreachable_unit_is_waited_for_then_failed_once(me_inst):
    """Adopter can't reach the execution node. While the unit can't be read, adoption waits: the job
    stays running and the unit is kept. Past the adoption deadline the job is failed. Once failed, a
    later adoption that can reach the unit again must not replay it into a second result.
    """
    clock = FakeClock()
    job = running_job(me_inst.hostname)
    unit = FakeWorkUnit(make_events(10), status_error=RuntimeError('no route to receptor-1'))
    work = FakeReceptorWork({UNIT: unit})

    for _ in range(2):
        adopt_job(job.id, open_work=lambda: work, clock=clock)
        clock.advance(60)
    job.refresh_from_db()
    assert job.status == 'running'
    assert ('release', UNIT) not in work.calls

    clock.advance(TIMEOUT)
    adopt_job(job.id, open_work=lambda: work, clock=clock)
    unit.status_error = None
    adopt_job(job.id, open_work=lambda: work, clock=clock)

    job.refresh_from_db()
    assert job.status == 'failed'
    assert RecordingDispatcher.dispatched == []


@pytest.mark.xfail(strict=True, reason='AAP-96857: an adopted job that timed out does not say so')
@pytest.mark.django_db
def test_adopted_job_that_timed_out_says_so(me_inst):
    """Job timeout while orphaned. The timeout is enforced on the execution node, so the unit ends with
    runner status "timeout". The adopted job must say it timed out, as a normal run does, so an operator
    can tell a timeout from a playbook failure.
    """
    job = running_job(me_inst.hostname)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), status='timeout', state='Failed')})

    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert job.status == 'failed'
    assert 'timeout' in job.job_explanation


@pytest.mark.xfail(strict=True, reason='AAP-96830: canceling a job whose controller is down is dropped; the job never ends canceled')
@pytest.mark.django_db
def test_cancel_requested_while_orphaned_cancels_the_unit(me_inst):
    """Cancel while orphaned. The user canceled while the controller was down, so the cancel reached no
    one. Today adoption never reads cancel_flag: it waits for the unit and finishes the job, successful,
    with cancel_flag set.
    """
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, cancel_flag=True)
    work = running_unit()

    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert ('cancel', UNIT) in work.calls
    assert job.status == 'canceled'


@pytest.mark.xfail(strict=True, reason='AAP-96835: canceling a job while it is finalized after a resume leaves it running forever')
@pytest.mark.django_db
def test_canceled_job_whose_unit_is_gone_is_finalized_canceled(me_inst):
    """Cancel during the adopter's finalize. The cancel stopped the adoption after the unit was
    released but before the status was saved. Today every later adoption finds no unit and defers, so
    the job stays running forever.
    """
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, cancel_flag=True)

    adopt_job(job.id, open_work=lambda: FakeReceptorWork())

    job.refresh_from_db()
    assert job.status == 'canceled'


@pytest.mark.django_db
def test_adopted_slice_maps_only_its_own_hosts(me_inst, inventory):
    """Job slicing. Slice 1 of 2 over five hosts runs fp-h1, fp-h3 and fp-h5. The host map adoption
    rebuilds, which the stats event carries into host summaries, holds that share of the inventory and
    no other.
    """
    hosts = {name: inventory.hosts.create(name=name) for name in ('fp-h1', 'fp-h2', 'fp-h3', 'fp-h4', 'fp-h5')}
    job = running_job(me_inst.hostname, inventory=inventory, job_slice_number=1, job_slice_count=2)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(stats_event(make_events(5), ['fp-h1', 'fp-h3', 'fp-h5']))})

    adopt_job(job.id, open_work=lambda: work)

    stats = next(event for event in RecordingDispatcher.dispatched if event.get('event') == 'playbook_on_stats')
    assert stats['host_map'] == {name: hosts[name].id for name in ('fp-h1', 'fp-h3', 'fp-h5')}


@pytest.mark.django_db
def test_adopted_job_updates_host_pointers_and_inventory_counts(me_inst, inventory):
    """Host pointers and inventory counts. After an adopted job's stats are saved, each host points at
    this job, only the failed host is flagged, and the inventory's counts are recomputed, as after a
    normal run.
    """
    hostnames = ['dc-h1', 'dc-h2', 'dc-h3']
    hosts = {name: inventory.hosts.create(name=name) for name in hostnames}
    job = running_job(me_inst.hostname, inventory=inventory)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(stats_event(make_events(5), hostnames, failed=['dc-h2']))})

    adopt_job(job.id, open_work=lambda: work)
    save_dispatched_events()

    for name, host in hosts.items():
        assert host.latest_job == job, name
        assert host.latest_summary.failed == (name == 'dc-h2'), name
    inventory.refresh_from_db()
    assert (inventory.total_hosts, inventory.hosts_with_active_failures, inventory.has_active_failures) == (3, 1, True)


@pytest.mark.django_db
def test_adopted_job_maps_constructed_hosts_like_a_normal_run(me_inst, inventory, organization):
    """Constructed inventories. A job on a constructed inventory maps each host name to the
    constructed host, as a normal run does.
    """
    source = inventory.hosts.create(name='ci-h1')
    constructed = Inventory.objects.create(name='constructed', kind='constructed', organization=organization)
    constructed.input_inventories.add(inventory)
    constructed_host = constructed.hosts.create(name='ci-h1', instance_id=str(source.id))
    job = running_job(me_inst.hostname, inventory=constructed)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(stats_event(make_events(3), ['ci-h1']))})

    adopt_job(job.id, open_work=lambda: work)

    stats = next(event for event in RecordingDispatcher.dispatched if event.get('event') == 'playbook_on_stats')
    assert stats['host_map'] == {'ci-h1': constructed_host.id}


def host_events(hostnames):
    """Runner events for one task on each host, then the stats event."""
    events = make_events(len(hostnames) + 2)
    for event, hostname in zip(events[1:-1], hostnames):
        event['event_data'] = {'host': hostname}
    return events


@pytest.mark.xfail(strict=True, reason='AAP-96843: replayed events link to the wrong hosts after an inventory change')
@pytest.mark.django_db
def test_replayed_events_keep_the_host_ids_the_job_started_with(me_inst, inventory):
    """Host map after an inventory change. A normal run maps each host name to the id it had when the
    job started. Adoption rebuilds the map from the inventory as it is now, so after a change while the
    job was orphaned, replayed events lose the deleted and disabled hosts and point a recreated host at
    its new id.

    While the job is orphaned: delete fp-h2, recreate fp-h3, disable fp-h4.
    """
    hosts = {name: inventory.hosts.create(name=name) for name in ('fp-h1', 'fp-h2', 'fp-h3', 'fp-h4', 'fp-h5')}
    ids_at_start = {name: host.id for name, host in hosts.items()}
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, inventory=inventory)

    hosts['fp-h2'].delete()
    hosts['fp-h3'].delete()
    inventory.hosts.create(name='fp-h3')
    hosts['fp-h4'].enabled = False
    hosts['fp-h4'].save()

    work = FakeReceptorWork({UNIT: FakeWorkUnit(host_events(list(hosts)))})
    adopt_job(job.id, open_work=lambda: work)

    replayed = {event['host_name']: event.get('host_id') for event in RecordingDispatcher.dispatched if event.get('host_name')}
    assert replayed == ids_at_start


@pytest.mark.django_db
def test_adopted_job_output_has_no_gaps_or_overlaps(me_inst):
    """Stdout line numbers. The adopter replays the runner's own stream, so once the replayed events
    are saved the job's output covers every line once, in order.
    """
    job = running_job(me_inst.hostname)
    events = make_events(40)
    for event in events[:12]:
        JobEvent.objects.create(job=job, job_created=job.created, **{k: event[k] for k in ('counter', 'event', 'stdout', 'start_line', 'end_line', 'uuid')})
    work = FakeReceptorWork({UNIT: FakeWorkUnit(events)})

    adopt_job(job.id, open_work=lambda: work)
    save_dispatched_events()

    saved = list(JobEvent.objects.filter(job=job).order_by('start_line').values_list('counter', 'start_line', 'end_line'))
    assert [counter for counter, _, _ in saved] == list(range(1, 41))
    assert all(saved[i][2] == saved[i + 1][1] for i in range(len(saved) - 1))


@pytest.mark.django_db
def test_events_deleted_during_replay_stay_deleted(me_inst):
    """Event cleanup during replay. The job's saved events are deleted after the adopter read what was
    already saved. The replay skips everything at or below that point, so the deleted events stay
    deleted, and the job still finishes.
    """
    job = running_job(me_inst.hostname)
    for counter in range(1, 25):
        JobEvent.objects.create(job=job, counter=counter, event='runner_on_ok', job_created=job.created)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(82))})
    real_results = work.results

    def cleanup_then_results(unit_id, startpos=None):
        JobEvent.objects.filter(job_id=job.id).delete()
        return real_results(unit_id, startpos)

    work.results = cleanup_then_results
    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert job.status == 'successful'
    assert RecordingDispatcher.counters() == list(range(25, 83))


@pytest.mark.xfail(strict=True, reason='AAP-96852: a resumed job\'s original private data directory stays on disk after it ends')
@pytest.mark.django_db
def test_resumed_job_removes_its_original_private_data_dir(me_inst, settings):
    """Credentials left on disk. The job's private data directory from before the restart holds its
    inventory and extra variables. Adoption works in a new directory and removes only that one, so the
    original stays until cleanup_images_and_files, which runs every 3 hours, finds it older than 60
    minutes.
    """
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT)
    original = os.path.join(settings.AWX_ISOLATION_BASE_PATH, f'awx_{job.pk}_before_restart')
    os.makedirs(os.path.join(original, 'env'))
    with open(os.path.join(original, 'env', 'extravars'), 'w') as f:
        json.dump({'survey_password': 'secret'}, f)
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})

    adopt_job(job.id, open_work=lambda: work)

    job.refresh_from_db()
    assert job.status == 'successful'
    assert not os.path.exists(original), f'{original} is still on disk'
