from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from django.utils.timezone import timedelta

from awx.main.models import Instance
from awx.main.tasks.adoption_decisions import (
    JobAction,
    LostInstanceAction,
    adoption_slot_available,
    execution_node_reachable,
    find_lost_instances,
    live_controller_hostnames,
    mesh_hostnames,
    reap_explanation,
    routed_hostnames,
    room_for_another_controllers_job,
    drop_mesh_connected_control_nodes,
    drop_routed_remote_nodes,
    gate_lost_instances,
    lost_instance_disposition,
    lost_instance_job_action,
    running_job_action,
    stall_budget_exhausted,
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
        # a dead one. The decision has only last_seen to go on (AAP-96824; the expected
        # behavior is in test_scenarios_liveness.py).
        slow = make_instance(PEER, seconds_since_seen=125)
        lost, _ = find_lost_instances([slow], ME, NOW)
        assert lost == [slow]

    def test_clock_skew_on_the_judge_makes_a_healthy_peer_look_lost(self, heartbeat_settings):
        # The peer heartbeated just now by its own clock, but this instance's clock runs
        # five minutes ahead (AAP-96827; the expected behavior is in test_adoption_clock.py).
        peer = make_instance(PEER, seconds_since_seen=0)
        lost, _ = find_lost_instances([peer], ME, NOW + timedelta(minutes=5))
        assert lost == [peer]


class TestGateLostInstances:
    def test_mesh_ready_handles_every_lost_instance(self):
        lost = [make_instance(PEER), make_instance(EXEC, node_type='execution'), make_instance('hop-1', node_type='hop')]
        assert gate_lost_instances(lost, mesh_ready=lambda: True) == lost

    def test_mesh_not_ready_defers_only_control_nodes(self):
        control = make_instance(PEER)
        execution = make_instance(EXEC, node_type='execution')
        hop = make_instance('hop-1', node_type='hop')
        hybrid = make_instance('hybrid-1', node_type='hybrid')
        assert gate_lost_instances([control, execution, hop, hybrid], mesh_ready=lambda: False) == [execution, hop]

    def test_mesh_is_not_checked_when_nothing_is_lost(self):
        def mesh_ready():
            raise AssertionError('mesh checked with nothing lost')

        assert gate_lost_instances([], mesh_ready) == []


class TestDropRoutedRemoteNodes:
    def test_routed_execution_and_hop_nodes_are_not_lost(self):
        execution = make_instance(EXEC, node_type='execution')
        hop = make_instance('hop-1', node_type='hop')
        assert drop_routed_remote_nodes([execution, hop], {EXEC, 'hop-1'}) == []

    def test_unrouted_remote_nodes_stay_lost(self):
        execution = make_instance(EXEC, node_type='execution')
        assert drop_routed_remote_nodes([execution], {PEER}) == [execution]

    def test_control_nodes_are_judged_by_the_mesh_gate_not_the_route(self):
        control = make_instance(PEER)
        assert drop_routed_remote_nodes([control], {PEER}) == [control]

    def test_unreadable_routing_table_keeps_every_lost_instance(self):
        execution = make_instance(EXEC, node_type='execution')
        assert drop_routed_remote_nodes([execution], None) == [execution]


class TestDropMeshConnectedControlNodes:
    def test_control_node_on_mesh_within_timeout_is_not_lost(self):
        # A slow controller: a few missed heartbeats, well inside the timeout (AAP-96824).
        slow = make_instance(PEER, seconds_since_seen=121)
        assert drop_mesh_connected_control_nodes([slow], {PEER}, NOW, timeout_seconds=300) == []

    def test_control_node_on_mesh_past_timeout_is_still_lost(self):
        # A hung dispatcher: the mesh connection survives, but last_seen is stale far past
        # the timeout, with nothing else to ever flip it off 'ready'.
        hung = make_instance(PEER, seconds_since_seen=301)
        assert drop_mesh_connected_control_nodes([hung], {PEER}, NOW, timeout_seconds=300) == [hung]

    def test_control_node_off_mesh_is_lost_regardless_of_timeout(self):
        gone = make_instance(PEER, seconds_since_seen=10)
        assert drop_mesh_connected_control_nodes([gone], set(), NOW, timeout_seconds=300) == [gone]

    def test_never_seen_control_node_on_mesh_is_lost(self):
        never_seen = make_instance(PEER, seconds_since_seen=None)
        assert drop_mesh_connected_control_nodes([never_seen], {PEER}, NOW, timeout_seconds=300) == [never_seen]

    def test_execution_and_hop_nodes_pass_through_unaffected(self):
        execution = make_instance(EXEC, node_type='execution', seconds_since_seen=10)
        hop = make_instance('hop-1', node_type='hop', seconds_since_seen=10)
        assert drop_mesh_connected_control_nodes([execution, hop], {EXEC, 'hop-1'}, NOW, timeout_seconds=300) == [execution, hop]


class TestLostInstanceDecisions:
    def decide(self, job, slot_available=True, route_available=True):
        return lost_instance_job_action(job, PEER, lambda: slot_available, lambda: route_available)

    def test_dispatched_job_of_a_lost_controller_is_adopted(self):
        assert self.decide(make_job(controller_node=PEER)) == JobAction.ADOPT

    def test_adoptable_job_is_deferred_when_this_controller_has_no_room(self):
        # It stays owned by the lost controller, so another controller's orphan sweep finds it.
        assert self.decide(make_job(controller_node=PEER), slot_available=False) == JobAction.DEFER

    def test_adoptable_job_is_deferred_when_this_node_has_no_route_to_its_execution_node(self):
        assert self.decide(make_job(controller_node=PEER), route_available=False) == JobAction.DEFER

    def test_routed_hostnames_reads_the_routing_table_not_the_gossiped_graph(self):
        status = {'RoutingTable': {'awx-1': 'awx-1'}, 'KnownConnectionCosts': {'receptor-hop': {'receptor-1': 1}}}

        assert routed_hostnames(status) == {'awx-1'}
        assert routed_hostnames({}) is None

    @pytest.mark.parametrize(
        'execution_node, on_mesh, expected',
        [('exec-1', {'exec-1'}, True), ('exec-1', {'other'}, False), ('exec-1', None, True), ('', {'other'}, True)],
    )
    def test_execution_node_reachable_declines_only_on_positive_evidence(self, execution_node, on_mesh, expected):
        assert execution_node_reachable(execution_node, on_mesh) is expected

    def test_job_that_never_reached_an_execution_environment_goes_back_to_pending(self):
        assert self.decide(make_job(controller_node=PEER, work_unit_id='', started=None)) == JobAction.REQUEUE

    @pytest.mark.parametrize(
        'job_fields',
        [
            {'controller_node': PEER, 'work_unit_id': '', 'cancel_flag': True},  # a user cancel must not be undone
            {'controller_node': ME, 'work_unit_id': ''},  # started without a work unit, but the lost node did not control it
            {'controller_node': PEER, 'execution_node': PEER},  # the lost node ran the playbook too
            {'controller_node': ME, 'execution_node': PEER},  # only the execution node was lost
        ],
    )
    def test_job_that_cannot_be_adopted_is_reaped(self, job_fields):
        assert self.decide(make_job(**job_fields)) == JobAction.REAP

    @pytest.mark.parametrize('work_unit_id', ['', None])
    def test_started_job_that_never_got_a_work_unit_goes_back_to_pending(self, work_unit_id):
        # Claimed during the controller's death, before any work unit existed: nothing reached an
        # execution environment, so a re-dispatch cannot collide with partial work.
        assert self.decide(make_job(controller_node=PEER, work_unit_id=work_unit_id)) == JobAction.REQUEUE

    @pytest.mark.parametrize('job_fields', [{'started': None}, {'controller_node': PEER}])
    def test_sync_job_is_reaped_not_requeued(self, job_fields):
        # The task manager never dispatches launch_type='sync', so a requeued one would sit pending forever.
        assert self.decide(make_job(work_unit_id='', launch_type='sync', **job_fields)) == JobAction.REAP

    @pytest.mark.parametrize('job_fields', [{'started': None}, {}])
    def test_job_submitted_to_receptor_without_a_saved_work_unit_is_reaped_not_requeued(self, job_fields):
        # receptor may have started the unit before the controller died, so a requeue could run the playbook twice.
        job = make_job(controller_node=PEER, work_unit_id='', job_env={'receptor_submit_started': True}, **job_fields)
        assert self.decide(job) == JobAction.REAP
        assert f'may still be running on {EXEC}' in reap_explanation(job, 'default')

    def test_reap_explanation_keeps_the_default_when_no_playbook_can_be_running(self):
        assert reap_explanation(make_job(work_unit_id=''), 'default') == 'default'
        assert reap_explanation(make_job(job_env={'receptor_submit_started': True}), 'default') == 'default'

    def test_capacity_is_asked_only_for_a_job_that_would_be_adopted(self):
        def slot_available():
            raise AssertionError('capacity was read for a job that is reaped anyway')

        assert lost_instance_job_action(make_job(controller_node=PEER, work_unit_id='', cancel_flag=True), PEER, slot_available) == JobAction.REAP

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


class TestAdoptionSlotAvailable:
    IMPACT = 1  # AWX_CONTROL_NODE_TASK_IMPACT

    def test_room_left_takes_the_job(self):
        assert adoption_slot_available(capacity=10, remaining_capacity=3) is True

    def test_job_that_exactly_fills_this_controller_is_taken(self):
        # 4.3: after the claim the job is already counted, so zero remaining means it fits exactly.
        assert adoption_slot_available(capacity=10, remaining_capacity=0) is True

    def test_controller_over_capacity_defers(self):
        # 4.16, 4.22: overcommitted after earlier adoptions, or scaled down mid-adoption.
        assert adoption_slot_available(capacity=10, remaining_capacity=-1) is False

    def test_asking_before_the_claim_needs_headroom_for_the_job(self):
        # 4.9: the job is not counted yet, so a controller at exactly capacity has no room for it.
        assert adoption_slot_available(capacity=10, remaining_capacity=0, headroom_needed=self.IMPACT) is False
        assert adoption_slot_available(capacity=10, remaining_capacity=1, headroom_needed=self.IMPACT) is True

    def test_unsized_or_draining_controller_does_not_block_adoption(self):
        # Zero capacity means not yet sized by the capacity job, or draining. Neither is "no room".
        assert adoption_slot_available(capacity=0, remaining_capacity=-5, headroom_needed=self.IMPACT) is True


class TestLiveControllerHostnames:
    GRACE = 120

    def live(self, *instances):
        return live_controller_hostnames(instances, NOW, self.GRACE)

    @pytest.mark.parametrize('node_state', ['ready', 'installed'])
    def test_ready_or_installed_instance_is_live(self, node_state):
        assert self.live(make_instance(PEER, node_state=node_state, seconds_since_seen=10_000)) == {PEER}

    def test_instance_unavailable_after_a_recent_check_in_is_still_live(self):
        # AAP-96708: one failed Redis ping marks a running controller unavailable. Sweeping its
        # jobs then ran them three times over.
        assert self.live(make_instance(PEER, node_state='unavailable', seconds_since_seen=self.GRACE)) == {PEER}

    def test_instance_unavailable_past_the_grace_period_is_not_live(self):
        assert self.live(make_instance(PEER, node_state='unavailable', seconds_since_seen=self.GRACE + 1)) == set()

    def test_unavailable_instance_never_seen_is_not_live(self):
        assert self.live(make_instance(PEER, node_state='unavailable', seconds_since_seen=None)) == set()

    def test_draining_instance_is_live(self):
        # 4.8 A controller set to drain is still running its jobs.
        assert self.live(make_instance(PEER, node_state='deprovisioning', seconds_since_seen=10_000)) == {PEER}

    @pytest.mark.parametrize('node_state', ['provisioning', 'provision-fail', 'deprovision-fail'])
    def test_instance_in_any_other_state_is_not_live(self, node_state):
        assert self.live(make_instance(PEER, node_state=node_state)) == set()

    def test_controller_without_a_row_is_live_while_it_is_on_the_mesh(self):
        # 2.4 Deprovisioning a live controller deletes its row while it still streams its jobs.
        assert live_controller_hostnames([], NOW, self.GRACE, mesh_hostnames={PEER}) == {PEER}

    def test_controller_without_a_row_and_off_the_mesh_is_not_live(self):
        assert PEER not in live_controller_hostnames([], NOW, self.GRACE, mesh_hostnames={EXEC})

    def test_departed_controller_is_not_live_while_its_connection_lingers(self):
        # A controller that announced its shutdown keeps its row, unavailable and back-dated;
        # its jobs are swept at once even though its receptor has not dropped off the mesh yet.
        departed = make_instance(PEER, node_state='unavailable', seconds_since_seen=self.GRACE + 1)
        assert live_controller_hostnames([departed], NOW, self.GRACE, mesh_hostnames={PEER}) == set()


class TestMeshHostnames:
    def test_every_node_named_in_the_routing_table_is_on_the_mesh(self):
        status = {'KnownConnectionCosts': {ME: {PEER: 1, EXEC: 1}, PEER: {ME: 1}}}
        assert mesh_hostnames(status) == {ME, PEER, EXEC}

    def test_node_that_left_the_mesh_stays_in_the_table_without_connections(self):
        status = {'KnownConnectionCosts': {ME: {EXEC: 1}, PEER: {}, EXEC: {ME: 1}}}
        assert mesh_hostnames(status) == {ME, EXEC}

    @pytest.mark.parametrize('status', [{}, {'KnownConnectionCosts': None}, {'KnownConnectionCosts': {}}])
    def test_empty_routing_table_puts_no_one_on_the_mesh(self, status):
        assert mesh_hostnames(status) == set()


class TestRoomForAnotherControllersJob:
    IMPACT = 1

    def test_enabled_node_with_room_takes_the_job(self):
        assert room_for_another_controllers_job(enabled=True, capacity=10, remaining_capacity=3, headroom_needed=self.IMPACT) is True

    def test_node_without_headroom_for_the_job_declines(self):
        assert room_for_another_controllers_job(enabled=True, capacity=10, remaining_capacity=0, headroom_needed=self.IMPACT) is False

    def test_disabled_node_declines(self):
        # 4.3 The task manager would not place work on it, so it takes no one else's either.
        assert room_for_another_controllers_job(enabled=False, capacity=10, remaining_capacity=10, headroom_needed=self.IMPACT) is False

    def test_node_without_capacity_declines(self):
        # Zero capacity means draining or unsized: room for its own jobs, none for another's.
        assert room_for_another_controllers_job(enabled=True, capacity=0, remaining_capacity=0) is False


class TestStartupJobAction:
    def test_dispatched_job_is_adopted(self):
        assert startup_job_action(make_job(work_unit_id='unit-1')) == JobAction.ADOPT

    @pytest.mark.parametrize('work_unit_id', ['', None])
    def test_undispatched_job_is_reaped(self, work_unit_id):
        assert startup_job_action(make_job(work_unit_id=work_unit_id)) == JobAction.REAP


class TestRunningJobAction:
    def decide(self, job, active_task_ids=('other-task',), ref_time=NOW, live_controllers=(ME,)):
        return running_job_action(job, ME, list(active_task_ids), ref_time, WORKFLOW_CTYPE, live_controllers)

    def test_orphan_this_instance_controls_is_adopted(self):
        assert self.decide(make_job()) == JobAction.ADOPT

    def test_job_a_dispatcher_task_still_tracks_is_left_alone(self):
        assert self.decide(make_job(celery_task_id='task-1'), active_task_ids=['task-1']) == JobAction.SKIP

    def test_orphan_with_cancel_requested_and_no_work_unit_is_reaped(self):
        # A user cancel must not be undone by putting the job back in the queue.
        assert self.decide(make_job(work_unit_id='', cancel_flag=True)) == JobAction.REAP

    @pytest.mark.parametrize('work_unit_id', ['', None])
    def test_running_orphan_that_never_got_a_work_unit_is_requeued(self, work_unit_id):
        # It was claimed during a controller kill, before any work unit existed, so nothing
        # reached an execution environment and a re-dispatch cannot collide with partial work.
        assert self.decide(make_job(work_unit_id=work_unit_id, execution_node='')) == JobAction.REQUEUE

    def test_running_sync_orphan_without_a_work_unit_is_reaped(self):
        # The task manager never dispatches launch_type='sync', so a requeued one would sit pending forever.
        assert self.decide(make_job(work_unit_id='', execution_node='', launch_type='sync')) == JobAction.REAP

    def test_running_orphan_submitted_to_receptor_without_a_saved_work_unit_is_reaped(self):
        # receptor may have started the unit, so a requeue could run the playbook twice.
        assert self.decide(make_job(work_unit_id='', execution_node='', job_env={'receptor_submit_started': True})) == JobAction.REAP

    def test_orphan_this_instance_only_executes_is_left_to_the_sweep(self):
        # A dispatched job this instance only executes, for a controller that isn't live: this
        # instance can't adopt it, and the orphan sweep will.
        assert self.decide(make_job(controller_node=PEER, execution_node=ME)) == JobAction.SKIP

    def test_orphan_this_instance_only_executes_for_a_live_controller_is_left_to_it(self):
        assert self.decide(make_job(controller_node=PEER, execution_node=ME, work_unit_id=''), live_controllers=(ME, PEER)) == JobAction.SKIP

    def test_undispatched_orphan_this_instance_only_executes_is_reaped(self):
        # Nothing to adopt and no live controller to hand it back to.
        assert self.decide(make_job(controller_node=PEER, execution_node=ME, work_unit_id='')) == JobAction.REAP

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


class TestStallBudget:
    TIMEOUT = 300

    def exhausted(self, stalled_for, last_event_ago=None):
        stalled_since = None if stalled_for is None else NOW - timedelta(seconds=stalled_for)
        last_event = None if last_event_ago is None else NOW - timedelta(seconds=last_event_ago)
        return stall_budget_exhausted(stalled_since, last_event, NOW, self.TIMEOUT)

    def test_stall_within_the_budget_waits(self):
        assert not self.exhausted(stalled_for=self.TIMEOUT)

    def test_stall_past_the_budget_is_exhausted(self):
        assert self.exhausted(stalled_for=self.TIMEOUT + 1)

    def test_quiet_job_is_not_failed_on_its_first_stall(self):
        # AAP-96829: a playbook task can run silently for longer than the timeout. The budget
        # starts at the first stall this controller records, not at the last event.
        assert not self.exhausted(stalled_for=1, last_event_ago=self.TIMEOUT * 10)

    def test_event_saved_after_the_stall_began_restarts_the_budget(self):
        assert not self.exhausted(stalled_for=self.TIMEOUT * 2, last_event_ago=10)

    def test_event_saved_before_the_stall_began_does_not_extend_it(self):
        assert self.exhausted(stalled_for=self.TIMEOUT + 1, last_event_ago=self.TIMEOUT * 2)

    def test_unknown_stall_start_never_exhausts_the_budget(self):
        # A lost cache entry only restarts the budget, which defers longer but never fails early.
        assert not self.exhausted(stalled_for=None, last_event_ago=self.TIMEOUT * 10)
