from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from django.utils.timezone import timedelta

from awx.main.models import Instance
from awx.main.tasks.adoption_decisions import (
    JobAction,
    LostInstanceAction,
    adoption_deadline_passed,
    find_lost_instances,
    gate_lost_instances,
    lost_instance_disposition,
    lost_instance_job_action,
    running_job_action,
    startup_job_action,
)

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
ME = 'awx-1'
PEER = 'awx-2'
EXEC = 'receptor-1'
WORKFLOW_CTYPE = 99
JOB_CTYPE = 1


def make_job(**kwargs):
    fields = dict(
        status='running',
        controller_node=ME,
        execution_node=EXEC,
        polymorphic_ctype_id=JOB_CTYPE,
        celery_task_id='task-1',
        started=NOW - timedelta(minutes=5),
        work_unit_id='unit-1',
    )
    fields.update(kwargs)
    return SimpleNamespace(**fields)


def make_instance(hostname, node_type='control', seconds_since_seen=0, node_state='ready'):
    last_seen = None if seconds_since_seen is None else NOW - timedelta(seconds=seconds_since_seen)
    return Instance(hostname=hostname, node_type=node_type, node_state=node_state, last_seen=last_seen)


@pytest.fixture
def heartbeat_settings(settings):
    settings.CLUSTER_NODE_HEARTBEAT_PERIOD = 60
    settings.CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE = 2
    settings.RECEPTOR_SERVICE_ADVERTISEMENT_PERIOD = 60
    return settings


class TestFindLostInstances:
    def test_peer_within_grace_period_is_not_lost(self, heartbeat_settings):
        peer = make_instance(PEER, seconds_since_seen=119)
        lost, remaining = find_lost_instances([peer], ME, NOW)
        assert lost == []
        assert remaining == [peer]

    def test_peer_past_grace_period_is_lost(self, heartbeat_settings):
        peer = make_instance(PEER, seconds_since_seen=121)
        lost, remaining = find_lost_instances([peer], ME, NOW)
        assert lost == [peer]
        assert remaining == []

    def test_peer_never_seen_is_lost(self, heartbeat_settings):
        peer = make_instance(PEER, seconds_since_seen=None)
        lost, _ = find_lost_instances([peer], ME, NOW)
        assert lost == [peer]

    def test_this_instance_is_never_lost_here(self, heartbeat_settings):
        me = make_instance(ME, seconds_since_seen=10_000)
        lost, remaining = find_lost_instances([me], ME, NOW)
        assert lost == []
        assert remaining == [me]

    def test_execution_node_gets_advertisement_period_added(self, heartbeat_settings):
        node = make_instance(EXEC, node_type='execution', seconds_since_seen=150)
        lost, _ = find_lost_instances([node], ME, NOW)
        assert lost == []

    def test_slow_controller_is_judged_lost_while_still_running(self, heartbeat_settings):
        # A controller whose heartbeat is delayed past the grace period looks exactly like
        # a dead one. The decision has only last_seen to go on.
        slow = make_instance(PEER, seconds_since_seen=125)
        lost, _ = find_lost_instances([slow], ME, NOW)
        assert lost == [slow]

    def test_clock_skew_on_the_judge_makes_a_healthy_peer_look_lost(self, heartbeat_settings):
        # The peer heartbeated just now by its own clock, but this instance's clock runs
        # five minutes ahead.
        peer = make_instance(PEER, seconds_since_seen=0)
        lost, _ = find_lost_instances([peer], ME, NOW + timedelta(minutes=5))
        assert lost == [peer]


class TestGateLostInstances:
    def test_mesh_ready_handles_every_lost_instance(self):
        lost = [make_instance(PEER), make_instance(EXEC, node_type='execution'), make_instance('hop-1', node_type='hop')]
        assert gate_lost_instances(lost, mesh_ready=True) == lost

    def test_mesh_not_ready_defers_only_control_nodes(self):
        control = make_instance(PEER)
        execution = make_instance(EXEC, node_type='execution')
        hop = make_instance('hop-1', node_type='hop')
        hybrid = make_instance('hybrid-1', node_type='hybrid')
        assert gate_lost_instances([control, execution, hop, hybrid], mesh_ready=False) == [execution, hop]


class TestLostInstanceDecisions:
    @pytest.mark.parametrize('work_unit_id', ['unit-1', ''])
    def test_jobs_of_a_lost_instance_are_reaped(self, work_unit_id):
        assert lost_instance_job_action(make_job(controller_node=PEER, work_unit_id=work_unit_id)) == JobAction.REAP

    @pytest.mark.parametrize(
        'node_type, node_state, auto_deprovision, expected',
        [
            ('control', 'ready', True, LostInstanceAction.DEPROVISION),
            ('control', 'unavailable', True, LostInstanceAction.DEPROVISION),
            ('execution', 'ready', True, LostInstanceAction.MARK_OFFLINE),
            ('control', 'ready', False, LostInstanceAction.MARK_OFFLINE),
            ('control', 'unavailable', False, LostInstanceAction.NONE),
            ('control', 'installed', False, LostInstanceAction.NONE),
            ('execution', 'unavailable', True, LostInstanceAction.NONE),
        ],
    )
    def test_disposition(self, node_type, node_state, auto_deprovision, expected):
        inst = make_instance(PEER, node_type=node_type, node_state=node_state)
        assert lost_instance_disposition(inst, auto_deprovision) == expected


class TestStartupJobAction:
    def test_dispatched_job_is_adopted(self):
        assert startup_job_action(make_job(work_unit_id='unit-1')) == JobAction.ADOPT

    @pytest.mark.parametrize('work_unit_id', ['', None])
    def test_undispatched_job_is_reaped(self, work_unit_id):
        assert startup_job_action(make_job(work_unit_id=work_unit_id)) == JobAction.REAP


class TestRunningJobAction:
    def decide(self, job, active_task_ids=('other-task',), ref_time=NOW):
        return running_job_action(job, ME, list(active_task_ids), ref_time, WORKFLOW_CTYPE)

    def test_orphan_this_instance_controls_is_adopted(self):
        assert self.decide(make_job()) == JobAction.ADOPT

    def test_job_a_dispatcher_task_still_tracks_is_left_alone(self):
        assert self.decide(make_job(celery_task_id='task-1'), active_task_ids=['task-1']) == JobAction.SKIP

    def test_orphan_not_yet_dispatched_to_receptor_is_reaped(self):
        assert self.decide(make_job(work_unit_id='')) == JobAction.REAP

    def test_orphan_this_instance_only_executes_is_reaped(self):
        # A hybrid node running a job for another controller: it can't adopt, so it reaps.
        assert self.decide(make_job(controller_node=PEER, execution_node=ME)) == JobAction.REAP

    def test_job_of_another_instance_is_left_alone(self):
        assert self.decide(make_job(controller_node=PEER)) == JobAction.SKIP

    @pytest.mark.parametrize('status', ['pending', 'waiting', 'successful', 'failed', 'canceled'])
    def test_job_not_running_is_left_alone(self, status):
        assert self.decide(make_job(status=status)) == JobAction.SKIP

    def test_workflow_job_is_left_alone(self):
        assert self.decide(make_job(polymorphic_ctype_id=WORKFLOW_CTYPE)) == JobAction.SKIP

    def test_job_started_after_ref_time_is_left_alone(self):
        assert self.decide(make_job(started=NOW + timedelta(seconds=1))) == JobAction.SKIP

    def test_job_without_start_time_is_left_alone(self):
        assert self.decide(make_job(started=None)) == JobAction.SKIP

    def test_no_ref_time_considers_every_start_time(self):
        assert self.decide(make_job(started=NOW + timedelta(days=1)), ref_time=None) == JobAction.ADOPT

    def test_empty_active_list_treats_every_job_as_orphaned(self):
        assert self.decide(make_job(), active_task_ids=()) == JobAction.ADOPT


class TestAdoptionDeadline:
    TIMEOUT = 300

    def test_recent_event_is_within_deadline(self):
        assert not adoption_deadline_passed(NOW - timedelta(seconds=299), NOW - timedelta(hours=1), NOW, self.TIMEOUT)

    def test_old_last_event_is_past_deadline(self):
        assert adoption_deadline_passed(NOW - timedelta(seconds=301), NOW - timedelta(hours=1), NOW, self.TIMEOUT)

    def test_last_event_wins_over_start_time(self):
        # A long job that is still producing events is not timed out by its age.
        assert not adoption_deadline_passed(NOW - timedelta(seconds=10), NOW - timedelta(days=1), NOW, self.TIMEOUT)

    def test_start_time_used_when_no_events(self):
        assert adoption_deadline_passed(None, NOW - timedelta(seconds=301), NOW, self.TIMEOUT)
        assert not adoption_deadline_passed(None, NOW - timedelta(seconds=299), NOW, self.TIMEOUT)

    def test_job_with_no_events_or_start_is_never_past_deadline(self):
        assert not adoption_deadline_passed(None, None, NOW, self.TIMEOUT)

    def test_quiet_job_is_past_deadline_even_while_healthy(self):
        # A playbook task that runs silently longer than the timeout (a long pause, a slow
        # package install) looks the same as a dead one.
        last_event = NOW - timedelta(seconds=self.TIMEOUT + 1)
        assert adoption_deadline_passed(last_event, NOW - timedelta(seconds=self.TIMEOUT + 60), NOW, self.TIMEOUT)
