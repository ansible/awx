"""Heartbeat and adoption decisions as of a chosen time, using an injected clock.

Each test sets the time instead of sleeping, so thresholds and clock skew between
controllers are checked exactly and in milliseconds.
"""

from unittest import mock

import pytest
from django.core.cache import cache
from django.utils.timezone import now, timedelta

from awx.main.models import Instance, Job, JobEvent
from awx.main.tasks import system
from awx.main.tasks.receptor import _adoption_stall_key
from awx.main.tasks.system import _heartbeat_instance_management, _sweep_orphaned_jobs, adopt_job, run_heartbeat
from awx.main.tests.fake_clock import FakeClock
from awx.main.tests.fake_receptor import FakeReceptorWork, FakeWorkUnit, RecordingDispatcher, make_events

GRACE = 120  # CLUSTER_NODE_HEARTBEAT_PERIOD * CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE
TIMEOUT = 300  # HADR_JOB_ADOPTION_TIMEOUT
UNIT = 'unit-1'


@pytest.fixture
def heartbeat_settings(settings):
    settings.CLUSTER_HOST_ID = 'ctrl-0'
    settings.AWX_AUTO_DEPROVISION_INSTANCES = False
    settings.CLUSTER_NODE_HEARTBEAT_PERIOD = 60
    settings.CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE = 2
    return settings


def control_node(hostname, last_seen):
    return Instance.objects.create(hostname=hostname, node_type='control', node_state='ready', last_seen=last_seen)


def lost_hostnames(clock):
    """Run ctrl-0's heartbeat at clock() and return the peers it judges lost."""
    # ctrl-0 is alive: its own last heartbeat was written by its own clock.
    Instance.objects.filter(hostname='ctrl-0').update(last_seen=clock())
    ctl = mock.MagicMock()
    # ctrl-0 has no route to the peer, so the judgement rests on last_seen alone.
    ctl.simple_command.return_value = {'KnownConnectionCosts': {'ctrl-0': {}}, 'Advertisements': []}
    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl', return_value=ctl),
        mock.patch('awx.main.tasks.system.inspect_execution_and_hop_nodes'),
        mock.patch.object(Instance, 'local_health_check'),
    ):
        _, _, lost, _ = _heartbeat_instance_management(clock)
    return sorted(inst.hostname for inst in lost)


# ── Clock skew between controllers ───────────────────────────────────────────


@pytest.mark.django_db
def test_peer_is_lost_only_after_the_grace_period(heartbeat_settings):
    t = now()
    control_node('ctrl-0', t)
    control_node('ctrl-1', t)
    clock = FakeClock(t)

    clock.advance(GRACE)
    assert lost_hostnames(clock) == []
    clock.advance(1)
    assert lost_hostnames(clock) == ['ctrl-1']


@pytest.mark.xfail(strict=True, reason='AAP-96827: a controller with a fast clock marks a healthy peer lost')
@pytest.mark.django_db
def test_judge_with_a_fast_clock_does_not_find_a_healthy_peer_lost(heartbeat_settings):
    # 2.8 Clock skew. ctrl-0's clock runs five minutes fast, so its own last_seen is five
    # minutes ahead. ctrl-1 heartbeated just now by the correct clock and is healthy.
    # Today ctrl-0 judges it by its own clock and finds it lost.
    t = now()
    control_node('ctrl-0', t + timedelta(minutes=5))
    control_node('ctrl-1', t)

    assert lost_hostnames(FakeClock(t + timedelta(minutes=5))) == []


@pytest.mark.django_db
def test_dead_peer_with_a_fast_clock_is_found_late(heartbeat_settings):
    # ctrl-1 ran five minutes fast and then died. Its last_seen is in the future, so a
    # correct judge only finds it lost once real time passes last_seen plus the grace period.
    t = now()
    control_node('ctrl-0', t)
    control_node('ctrl-1', t + timedelta(minutes=5))
    clock = FakeClock(t)

    clock.advance(5 * 60 + GRACE)
    assert lost_hostnames(clock) == []
    clock.advance(1)
    assert lost_hostnames(clock) == ['ctrl-1']


# ── Adoption deadline, end to end ─────────────────────────────────────────────


@pytest.fixture
def adoption_env(settings, tmp_path):
    settings.AWX_ISOLATION_BASE_PATH = str(tmp_path)
    settings.HADR_JOB_ADOPTION_TIMEOUT = TIMEOUT
    RecordingDispatcher.reset()
    with (
        mock.patch('awx.main.tasks.receptor.connections'),
        mock.patch('awx.main.tasks.callback.CallbackQueueDispatcher', RecordingDispatcher),
        mock.patch('awx.main.tasks.jobs.ScheduleTaskManager'),
        mock.patch('awx.main.tasks.jobs.ScheduleWorkflowManager'),
        mock.patch('awx.main.models.unified_jobs.UnifiedJob.websocket_emit_status'),
    ):
        yield


@pytest.fixture
def orphan(me_inst):
    """A running job whose last saved event was written at the returned time."""
    started = now() - timedelta(hours=1)
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=UNIT, started=started)
    JobEvent.objects.create(job=job, counter=1, event='playbook_on_start', job_created=job.created)
    last_event = now() - timedelta(minutes=10)
    JobEvent.objects.filter(job=job).update(created=last_event)
    return job, last_event


@pytest.mark.django_db
def test_orphan_within_the_deadline_is_adopted(adoption_env, orphan):
    job, last_event = orphan
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})
    clock = FakeClock(last_event + timedelta(seconds=TIMEOUT - 1))

    adopt_job(job.id, open_work=lambda: work, clock=clock)

    job.refresh_from_db()
    assert job.status == 'successful'
    # finished is when the playbook ended, taken from its last event, never after the adoption.
    assert job.started <= job.finished <= clock()
    assert RecordingDispatcher.counters() == list(range(2, 11))
    assert ('close',) in work.calls


@pytest.mark.django_db
def test_orphan_silent_past_the_deadline_is_still_streamed_while_its_unit_answers(adoption_env, orphan):
    # Silence since the last event is not a deadline: a quiet playbook looks the same
    # (AAP-96829). Only a unit that cannot be reached is failed, after the stall budget.
    job, last_event = orphan
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})

    adopt_job(job.id, open_work=lambda: work, clock=FakeClock(last_event + timedelta(seconds=TIMEOUT + 1)))

    job.refresh_from_db()
    assert job.status == 'successful'


@pytest.mark.django_db
@pytest.mark.parametrize('unit_status', ['successful', 'timeout'])
def test_reachable_unit_with_unprocessed_events_is_drained_and_finalized_not_reaped(adoption_env, orphan, unit_status):
    # TC-11. event_processing_finished is False and the adoption timeout has long passed, but the
    # unit answers and still holds events AWX never saw. AWX must drain them and finalize from the
    # unit's own result; HADR_JOB_ADOPTION_TIMEOUT applies only to a unit it cannot reach.
    job, last_event = orphan
    assert job.event_processing_finished is False
    unit = FakeWorkUnit(make_events(10), status=unit_status, state='Failed' if unit_status == 'timeout' else None)
    work = FakeReceptorWork({UNIT: unit})
    clock = FakeClock(last_event + timedelta(seconds=TIMEOUT * 10))

    adopt_job(job.id, open_work=lambda: work, clock=clock)

    job.refresh_from_db()
    assert RecordingDispatcher.counters() == list(range(2, 11))
    assert 'HADR_JOB_ADOPTION_TIMEOUT' not in job.job_explanation
    if unit_status == 'timeout':
        assert job.status == 'failed'
        assert 'timeout' in job.job_explanation
    else:
        assert job.status == 'successful'


# ── Stall budgets on the injected clock ──────────────────────────────────────


@pytest.mark.django_db
def test_unreachable_unit_is_failed_once_unreachable_past_the_budget(adoption_env, orphan):
    # 3.9 on the clock: the budget starts at the first failed status query, not the last event.
    cache.clear()
    job, _ = orphan
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10), status_error=RuntimeError('no route to receptor-1'))})
    clock = FakeClock()

    adopt_job(job.id, open_work=lambda: work, clock=clock)
    clock.advance(TIMEOUT)
    adopt_job(job.id, open_work=lambda: work, clock=clock)
    job.refresh_from_db()
    assert job.status == 'running'

    clock.advance(1)
    adopt_job(job.id, open_work=lambda: work, clock=clock)
    job.refresh_from_db()
    assert job.status == 'failed'


@pytest.mark.django_db
def test_capacity_wait_is_measured_on_the_injected_clock(adoption_env, orphan):
    cache.clear()
    job, _ = orphan
    opened = mock.Mock()
    clock = FakeClock()

    with mock.patch('awx.main.tasks.system._adoption_slot_available', return_value=False):
        adopt_job(job.id, open_work=opened, clock=clock)
        clock.advance(TIMEOUT + 1)
        adopt_job(job.id, open_work=opened, clock=clock)

    job.refresh_from_db()
    assert job.status == 'failed'
    opened.assert_not_called()


@pytest.mark.django_db
def test_stalled_stream_is_finalized_once_stalled_past_the_budget(adoption_env, orphan):
    # The stall watchdog itself runs on time.monotonic(); this drives what follows a stall.
    cache.clear()
    job, _ = orphan
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})
    clock = FakeClock()

    def stalled(receptor_job, _work):
        # The abandoned stream's processor raises, and _process_phase marks that as detached too.
        receptor_job.stream_stalled = True
        receptor_job.detached = True
        return None

    with mock.patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', stalled):
        adopt_job(job.id, open_work=lambda: work, clock=clock)
        job.refresh_from_db()
        assert job.status == 'running', 'a stalled stream defers'
        assert UNIT in work.units, 'and keeps the unit for a later attempt'

        clock.advance(TIMEOUT + 1)
        adopt_job(job.id, open_work=lambda: work, clock=clock)

    job.refresh_from_db()
    assert job.status == 'successful', 'past the budget the unit status decides'
    assert UNIT not in work.units, 'and the unit is released'


@pytest.mark.django_db
def test_cut_off_stream_fails_the_job_once_cut_off_past_the_budget(adoption_env, orphan):
    # The unit is not terminal: the local receptor still answers for it, the execution node is gone.
    cache.clear()
    job, _ = orphan
    work = FakeReceptorWork({UNIT: FakeWorkUnit(make_events(10))})
    clock = FakeClock()

    def cut_off(receptor_job, _work):
        receptor_job.stream_stalled = True
        receptor_job.stream_cut_off = True
        receptor_job.detached = True
        return None

    with (
        mock.patch('awx.main.tasks.receptor.AWXReceptorJob._process_phase', cut_off),
        mock.patch('awx.main.tasks.receptor._determine_adoption_status_from_unit', return_value=(None, None, False)),
    ):
        adopt_job(job.id, open_work=lambda: work, clock=clock)
        job.refresh_from_db()
        assert job.status == 'running', 'the wait is bounded, not skipped'

        clock.advance(TIMEOUT + 1)
        adopt_job(job.id, open_work=lambda: work, clock=clock)

    job.refresh_from_db()
    assert job.status == 'failed'
    assert 'unreachable' in job.job_explanation


# ── The orphan sweep on the injected clock ───────────────────────────────────


@pytest.mark.django_db
def test_sweep_takes_jobs_of_a_controller_unavailable_past_the_grace_period(heartbeat_settings, me_inst):
    seen = now()
    Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='unavailable', last_seen=seen)
    job = Job.objects.create(controller_node='ctrl-1', execution_node='receptor-1', status='running', work_unit_id=UNIT, started=seen)
    clock = FakeClock(seen + timedelta(seconds=GRACE))

    with (
        mock.patch('awx.main.tasks.system._adoption_slot_available', return_value=True),
        mock.patch('awx.main.tasks.system._publish_adoption') as publish,
    ):
        _sweep_orphaned_jobs(me_inst, clock=clock)
        publish.assert_not_called()

        clock.advance(1)
        _sweep_orphaned_jobs(me_inst, clock=clock)

    publish.assert_called_once()
    job.refresh_from_db()
    assert job.controller_node == 'ctrl-0'


@pytest.mark.django_db
def test_sweep_waits_for_a_node_with_a_route_but_only_for_the_adoption_timeout(heartbeat_settings, me_inst):
    """A node with no route to the execution node leaves the job to a peer that has one, but not
    forever: past HADR_JOB_ADOPTION_TIMEOUT it claims the job so it is not left with no owner (3.9)."""
    cache.clear()
    heartbeat_settings.HADR_JOB_ADOPTION_TIMEOUT = TIMEOUT
    seen = now()
    Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='unavailable', last_seen=seen - timedelta(hours=1))
    job = Job.objects.create(controller_node='ctrl-1', execution_node='receptor-1', status='running', work_unit_id=UNIT, started=seen)
    clock = FakeClock(seen)
    no_route = lambda: {'ctrl-0'}  # noqa: E731

    with (
        mock.patch('awx.main.tasks.system._adoption_slot_available', return_value=True),
        mock.patch('awx.main.tasks.system._publish_adoption') as publish,
    ):
        _sweep_orphaned_jobs(me_inst, clock=clock, route_lookup=no_route)
        publish.assert_not_called()
        assert cache.get(_adoption_stall_key(job, 'unreachable')) is not None, 'the wait is timed'

        clock.advance(TIMEOUT + 1)
        _sweep_orphaned_jobs(me_inst, clock=clock, route_lookup=no_route)

    publish.assert_called_once()
    job.refresh_from_db()
    assert job.controller_node == 'ctrl-0'
    cache.clear()


@pytest.mark.django_db
def test_sweep_clears_the_wait_once_a_route_exists(heartbeat_settings, me_inst):
    cache.clear()
    heartbeat_settings.HADR_JOB_ADOPTION_TIMEOUT = TIMEOUT
    seen = now()
    Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='unavailable', last_seen=seen - timedelta(hours=1))
    job = Job.objects.create(controller_node='ctrl-1', execution_node='receptor-1', status='running', work_unit_id=UNIT, started=seen)
    clock = FakeClock(seen)

    with (
        mock.patch('awx.main.tasks.system._adoption_slot_available', return_value=True),
        mock.patch('awx.main.tasks.system._publish_adoption') as publish,
    ):
        _sweep_orphaned_jobs(me_inst, clock=clock, route_lookup=lambda: {'ctrl-0'})
        assert cache.get(_adoption_stall_key(job, 'unreachable')) is not None
        _sweep_orphaned_jobs(me_inst, clock=clock, route_lookup=lambda: {'receptor-1'})

    publish.assert_called_once()
    assert cache.get(_adoption_stall_key(job, 'unreachable')) is None, 'a later cut gets a fresh budget'
    cache.clear()


@pytest.mark.django_db
def test_heartbeat_sweeps_on_its_own_clock(heartbeat_settings, me_inst):
    clock = FakeClock()
    with (
        mock.patch.object(system, '_heartbeat_instance_management', return_value=(me_inst, [], [], None)),
        mock.patch.object(system, '_get_active_task_ids_from_dispatcherd', return_value=[]),
        mock.patch.object(system, '_process_running_jobs'),
        mock.patch.object(system, '_sweep_orphaned_jobs') as sweep,
    ):
        run_heartbeat(mock.Mock(), clock=clock)

    assert sweep.call_args.kwargs['clock'] is clock
