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
    @pytest.mark.parametrize(
        'hostname, node_type, seconds_since_seen, judge_ahead, expected_lost',
        [
            pytest.param(PEER, 'control', 119, 0, False, id='peer-within-grace-period'),
            pytest.param(PEER, 'control', 121, 0, True, id='peer-past-grace-period'),
            pytest.param(PEER, 'control', None, 0, True, id='peer-never-seen'),
            pytest.param(ME, 'control', 10_000, 0, False, id='this-instance-is-never-lost-here'),
            pytest.param(EXEC, 'execution', 150, 0, False, id='execution-node-gets-advertisement-period-added'),
            # A controller whose heartbeat is delayed past the grace period looks exactly like
            # a dead one. The decision has only last_seen to go on (AAP-96824; the expected
            # behavior is in test_scenarios_liveness.py).
            pytest.param(PEER, 'control', 125, 0, True, id='slow-controller-is-judged-lost-while-still-running'),
            # The peer heartbeated just now by its own clock, but this instance's clock runs
            # five minutes ahead (AAP-96827; the expected behavior is in test_adoption_clock.py).
            pytest.param(PEER, 'control', 0, 300, True, id='clock-skew-on-the-judge-makes-a-healthy-peer-look-lost'),
        ],
    )
    def test_lost(self, heartbeat_settings, hostname, node_type, seconds_since_seen, judge_ahead, expected_lost):
        inst = make_instance(hostname, node_type=node_type, seconds_since_seen=seconds_since_seen)
        lost, remaining = find_lost_instances([inst], ME, NOW + timedelta(seconds=judge_ahead))
        assert lost == ([inst] if expected_lost else [])
        assert remaining == ([] if expected_lost else [inst])


class TestGateLostInstances:
    @pytest.mark.parametrize(
        'mesh_ready, handled_node_types',
        [
            pytest.param(True, ['control', 'execution', 'hop', 'hybrid'], id='mesh-ready-handles-every-lost-instance'),
            pytest.param(False, ['execution', 'hop'], id='mesh-not-ready-defers-only-control-nodes'),
        ],
    )
    def test_gate(self, mesh_ready, handled_node_types):
        lost = [make_instance(f'{node_type}-1', node_type=node_type) for node_type in ('control', 'execution', 'hop', 'hybrid')]
        handled = gate_lost_instances(lost, mesh_ready=lambda: mesh_ready)
        assert [inst.node_type for inst in handled] == handled_node_types

    def test_mesh_is_not_checked_when_nothing_is_lost(self):
        def mesh_ready():
            raise AssertionError('mesh checked with nothing lost')

        assert gate_lost_instances([], mesh_ready) == []


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
    @pytest.mark.parametrize(
        'work_unit_id, expected',
        [
            pytest.param('unit-1', JobAction.ADOPT, id='dispatched-job-is-adopted'),
            pytest.param('', JobAction.REAP, id='undispatched-job-is-reaped'),
            pytest.param(None, JobAction.REAP, id='job-without-work-unit-is-reaped'),
        ],
    )
    def test_startup_job_action(self, work_unit_id, expected):
        assert startup_job_action(make_job(work_unit_id=work_unit_id)) == expected


OTHER_TASK = ['other-task']


class TestRunningJobAction:
    @pytest.mark.parametrize(
        'job_fields, active_task_ids, ref_time, expected',
        [
            pytest.param({}, OTHER_TASK, NOW, JobAction.ADOPT, id='orphan-this-instance-controls-is-adopted'),
            pytest.param({'celery_task_id': 'task-1'}, ['task-1'], NOW, JobAction.SKIP, id='job-a-dispatcher-task-still-tracks-is-left-alone'),
            pytest.param({'work_unit_id': ''}, OTHER_TASK, NOW, JobAction.REAP, id='orphan-not-yet-dispatched-to-receptor-is-reaped'),
            # A hybrid node running a job for another controller: it can't adopt, so it reaps.
            pytest.param({'controller_node': PEER, 'execution_node': ME}, OTHER_TASK, NOW, JobAction.REAP, id='orphan-this-instance-only-executes-is-reaped'),
            pytest.param({'controller_node': PEER}, OTHER_TASK, NOW, JobAction.SKIP, id='job-of-another-instance-is-left-alone'),
            *[
                pytest.param({'status': status}, OTHER_TASK, NOW, JobAction.SKIP, id=f'{status}-job-is-left-alone')
                for status in ('pending', 'waiting', 'successful', 'failed', 'canceled')
            ],
            pytest.param({'polymorphic_ctype_id': WORKFLOW_CTYPE}, OTHER_TASK, NOW, JobAction.SKIP, id='workflow-job-is-left-alone'),
            pytest.param({'started': NOW + timedelta(seconds=1)}, OTHER_TASK, NOW, JobAction.SKIP, id='job-started-after-ref-time-is-left-alone'),
            pytest.param({'started': None}, OTHER_TASK, NOW, JobAction.SKIP, id='job-without-start-time-is-left-alone'),
            pytest.param({'started': NOW + timedelta(days=1)}, OTHER_TASK, None, JobAction.ADOPT, id='no-ref-time-considers-every-start-time'),
            pytest.param({}, [], NOW, JobAction.ADOPT, id='empty-active-list-treats-every-job-as-orphaned'),
        ],
    )
    def test_running_job_action(self, job_fields, active_task_ids, ref_time, expected):
        assert running_job_action(make_job(**job_fields), ME, active_task_ids, ref_time, WORKFLOW_CTYPE) == expected


def seconds_ago(seconds):
    return None if seconds is None else NOW - timedelta(seconds=seconds)


TIMEOUT = 300


class TestAdoptionDeadline:
    @pytest.mark.parametrize(
        'last_event_age, started_age, expected_passed',
        [
            pytest.param(299, 3600, False, id='recent-event-is-within-deadline'),
            pytest.param(301, 3600, True, id='old-last-event-is-past-deadline'),
            # A long job that is still producing events is not timed out by its age.
            pytest.param(10, 86400, False, id='last-event-wins-over-start-time'),
            pytest.param(None, 301, True, id='no-events-and-old-start-is-past-deadline'),
            pytest.param(None, 299, False, id='no-events-and-recent-start-is-within-deadline'),
            pytest.param(None, None, False, id='job-with-no-events-or-start-is-never-past-deadline'),
            # A playbook task that runs silently longer than the timeout (a long pause, a slow
            # package install) looks the same as a dead one (AAP-96829; the expected behavior
            # is in test_scenarios_adoption.py).
            pytest.param(TIMEOUT + 1, TIMEOUT + 60, True, id='quiet-job-is-past-deadline-even-while-healthy'),
        ],
    )
    def test_adoption_deadline_passed(self, last_event_age, started_age, expected_passed):
        assert adoption_deadline_passed(seconds_ago(last_event_age), seconds_ago(started_age), NOW, TIMEOUT) == expected_passed
