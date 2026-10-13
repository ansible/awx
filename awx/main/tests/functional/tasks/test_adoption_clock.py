"""Heartbeat and adoption decisions as of a chosen time, using an injected clock.

Each test sets the time instead of sleeping, so thresholds and clock skew between
controllers are checked exactly and in milliseconds.
"""

from unittest import mock

import pytest
from django.utils.timezone import now, timedelta

from awx.main.models import Instance, Job, JobEvent
from awx.main.tasks.system import _heartbeat_instance_management, adopt_job
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
    ctl.simple_command.return_value = {'KnownConnectionCosts': {'ctrl-0': {'ctrl-1': 1}}, 'Advertisements': []}
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


@pytest.mark.django_db
def test_judge_with_a_fast_clock_finds_a_healthy_peer_lost(heartbeat_settings):
    # ctrl-0's clock runs five minutes fast, so its own last_seen is five minutes ahead.
    # ctrl-1 heartbeated just now by the correct clock and is healthy.
    t = now()
    control_node('ctrl-0', t + timedelta(minutes=5))
    control_node('ctrl-1', t)

    assert lost_hostnames(FakeClock(t + timedelta(minutes=5))) == ['ctrl-1']


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
    assert job.finished == clock()
    assert RecordingDispatcher.counters() == list(range(2, 11))
    assert ('close',) in work.calls


@pytest.mark.django_db
def test_orphan_past_the_deadline_is_failed_without_contacting_receptor(adoption_env, orphan):
    job, last_event = orphan
    opened = mock.Mock()

    adopt_job(job.id, open_work=opened, clock=FakeClock(last_event + timedelta(seconds=TIMEOUT + 1)))

    job.refresh_from_db()
    assert job.status == 'failed'
    assert 'HADR_JOB_ADOPTION_TIMEOUT' in job.job_explanation
    opened.assert_not_called()
