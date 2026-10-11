"""A small cluster in the test database, for job adoption failure scenarios.

The scenarios were first found with the failpoint harness on a two-controller
docker-compose cluster. Here the same cluster is rows in the test database:

  ctrl-0      this controller, running the heartbeat under test
  ctrl-1      a peer controller, judged lost when its last_seen is stale
  receptor-1  the execution node the jobs run on

Receptor is replaced with FakeReceptorWork and the callback-receiver queue with
RecordingDispatcher (see awx.main.tests.fake_receptor), so the real heartbeat, reap,
adoption and finalize code runs without a mesh.
"""

import contextlib
from unittest import mock

from django.utils.timezone import now, timedelta

from awx.main.models import Instance
from awx.main.tasks.system import _heartbeat_handle_lost_instances, _heartbeat_instance_management
from awx.main.tests.fake_receptor import RecordingDispatcher

THIS = 'ctrl-0'
PEER = 'ctrl-1'
EXEC = 'receptor-1'
UNIT = 'unit-1'
GRACE = 120  # CLUSTER_NODE_HEARTBEAT_PERIOD * CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE


def configure(settings):
    settings.CLUSTER_HOST_ID = THIS
    settings.AWX_AUTO_DEPROVISION_INSTANCES = False
    settings.CLUSTER_NODE_HEARTBEAT_PERIOD = 60
    settings.CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE = 2


def make_cluster(peer_seconds_since_seen=GRACE + 80):
    """Create ctrl-0 (healthy), ctrl-1 (silent for peer_seconds_since_seen) and receptor-1."""
    t = now()
    this = Instance.objects.create(hostname=THIS, node_type='control', node_state='ready', last_seen=t)
    peer = Instance.objects.create(hostname=PEER, node_type='control', node_state='ready', last_seen=t - timedelta(seconds=peer_seconds_since_seen))
    Instance.objects.create(hostname=EXEC, node_type='execution', node_state='ready', last_seen=t)
    return this, peer


def mesh(*connected):
    """Receptor status as ctrl-0 sees it, with ctrl-0 connected to each node in connected."""
    return {'KnownConnectionCosts': {THIS: {node: 1 for node in connected}}, 'Advertisements': []}


def run_lost_instance_handling(mesh_status, work=None, clock=None):
    """Run ctrl-0's heartbeat up to and including lost-instance handling. Return the lost hostnames.

    work, when given, is returned wherever system.py opens ReceptorWork, so a test can see
    whether a work unit was canceled.
    """
    ctl = mock.MagicMock()
    ctl.simple_command.return_value = mesh_status
    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch('awx.main.tasks.system.get_receptor_ctl', return_value=ctl))
        stack.enter_context(mock.patch('awx.main.tasks.system.inspect_execution_and_hop_nodes'))
        stack.enter_context(mock.patch.object(Instance, 'local_health_check'))
        if work is not None:
            stack.enter_context(mock.patch('awx.main.tasks.system.ReceptorWork', return_value=work))
        this_inst, _, lost, _ = _heartbeat_instance_management(clock)
        _heartbeat_handle_lost_instances(lost, this_inst)
    return sorted(inst.hostname for inst in lost)


@contextlib.contextmanager
def adoption_env(settings, tmp_path):
    """Patch what adoption touches outside the database: Redis, websockets and the schedulers."""
    settings.AWX_ISOLATION_BASE_PATH = str(tmp_path)
    RecordingDispatcher.reset()
    # connections.close_all() would end the test's transaction; events go to the recorder instead of Redis.
    with (
        mock.patch('awx.main.tasks.receptor.connections'),
        mock.patch('awx.main.tasks.callback.CallbackQueueDispatcher', RecordingDispatcher),
        mock.patch('awx.main.tasks.jobs.ScheduleTaskManager'),
        mock.patch('awx.main.tasks.jobs.ScheduleWorkflowManager'),
        mock.patch('awx.main.models.unified_jobs.UnifiedJob.websocket_emit_status'),
    ):
        yield


def assert_playbook_not_left_running(job, work):
    """Fail when the job is no longer active but its work unit was never canceled."""
    job.refresh_from_db()
    still_active = job.status in ('running', 'waiting')
    unit_canceled = ('cancel', job.work_unit_id) in work.calls
    assert still_active or unit_canceled, f'job is {job.status!r} but its work unit {job.work_unit_id} was never canceled'
