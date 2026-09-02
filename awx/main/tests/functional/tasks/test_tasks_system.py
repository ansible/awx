import copy
import json
import logging
import os
import tempfile
import shutil
from contextlib import contextmanager
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from awx.main.tasks.system import (
    CleanupImagesAndFiles,
    execution_node_health_check,
    inspect_established_receptor_connections,
    clear_setting_cache,
    _batched_delete_inventory,
    _mesh_all_ready_nodes_visible,
    _heartbeat_handle_lost_instances,
    _reap_and_mark_lost_instance,
    inspect_execution_and_hop_nodes,
    _heartbeat_instance_management,
    _process_startup_jobs,
    _process_running_jobs,
    _startup_reap_undispatched,
    _try_adopt_job,
)
from awx.main.dispatch.reaper import reap
from awx.main.management.commands.dispatcherd import Command
from django.db import DatabaseError
from django.utils.timezone import now, timedelta

from awx.main.models import Instance, Inventory, Job, Organization, ReceptorAddress, InstanceLink, WorkflowJob
from awx.main.models.inventory import Group, Host


@pytest.mark.django_db
class TestLinkState:
    @pytest.fixture(autouse=True)
    def configure_settings(self, settings):
        settings.IS_K8S = True

    def test_inspect_established_receptor_connections(self):
        '''
        Change link state from ADDING to ESTABLISHED
        if the receptor status KnownConnectionCosts field
        has an entry for the source and target node.
        '''
        hop1 = Instance.objects.create(hostname='hop1')
        hop2 = Instance.objects.create(hostname='hop2')
        hop2addr = ReceptorAddress.objects.create(instance=hop2, address='hop2', port=5678)
        InstanceLink.objects.create(source=hop1, target=hop2addr, link_state=InstanceLink.States.ADDING)

        # calling with empty KnownConnectionCosts should not change the link state
        inspect_established_receptor_connections({"KnownConnectionCosts": {}})
        assert InstanceLink.objects.get(source=hop1, target=hop2addr).link_state == InstanceLink.States.ADDING

        mesh_state = {"KnownConnectionCosts": {"hop1": {"hop2": 1}}}
        inspect_established_receptor_connections(mesh_state)
        assert InstanceLink.objects.get(source=hop1, target=hop2addr).link_state == InstanceLink.States.ESTABLISHED


@pytest.fixture
def job_folder_factory(request):
    def _rf(job_id='1234'):
        pdd_path = tempfile.mkdtemp(prefix=f'awx_{job_id}_')

        def test_folder_cleanup():
            if os.path.exists(pdd_path):
                shutil.rmtree(pdd_path)

        request.addfinalizer(test_folder_cleanup)

        return pdd_path

    return _rf


@pytest.fixture
def mock_job_folder(job_folder_factory):
    return job_folder_factory()


@pytest.mark.django_db
@pytest.mark.parametrize('node_type', ('control. hybrid'))
def test_no_worker_info_on_AWX_nodes(node_type):
    hostname = 'us-south-3-compute.invalid'
    Instance.objects.create(hostname=hostname, node_type=node_type)
    assert execution_node_health_check(hostname) is None


@pytest.mark.django_db
def test_folder_cleanup_stale_file(mock_job_folder, mock_me):
    CleanupImagesAndFiles.run()
    assert os.path.exists(mock_job_folder)  # grace period should protect folder from deletion

    CleanupImagesAndFiles.run(grace_period=0)
    assert not os.path.exists(mock_job_folder)  # should be deleted


@pytest.mark.django_db
def test_folder_cleanup_running_job(mock_job_folder, me_inst):
    job = Job.objects.create(id=1234, controller_node=me_inst.hostname, status='running')
    CleanupImagesAndFiles.run(grace_period=0)
    assert os.path.exists(mock_job_folder)  # running job should prevent folder from getting deleted

    job.status = 'failed'
    job.save(update_fields=['status'])
    CleanupImagesAndFiles.run(grace_period=0)
    assert not os.path.exists(mock_job_folder)  # job is finished and no grace period, should delete


@pytest.mark.django_db
def test_folder_cleanup_multiple_running_jobs(job_folder_factory, me_inst):
    jobs = []
    dirs = []
    num_jobs = 3

    for i in range(num_jobs):
        job = Job.objects.create(controller_node=me_inst.hostname, status='running')
        dirs.append(job_folder_factory(job.id))
        jobs.append(job)

    CleanupImagesAndFiles.run(grace_period=0)

    assert [os.path.exists(d) for d in dirs] == [True for i in range(num_jobs)]


@pytest.mark.django_db
class TestBatchedDeleteInventory:
    def _make_inventory_with_hosts(self, count):
        from django.utils import timezone

        now = timezone.now()
        org = Organization.objects.create(name='test-org')
        inv = Inventory.objects.create(name='test-inv', organization=org)
        group = Group.objects.create(name='test-group', inventory=inv)
        hosts = [Host(name=f'host-{i}', inventory=inv, created=now, modified=now) for i in range(count)]
        Host.objects.bulk_create(hosts)
        group.hosts.set(Host.objects.filter(inventory=inv))
        return inv

    def test_deletes_all_hosts_and_inventory(self):
        inv = self._make_inventory_with_hosts(10)
        inv_id = inv.id
        _batched_delete_inventory(inv, batch_size=3)
        assert not Host.objects.filter(inventory_id=inv_id).exists()
        assert not Group.objects.filter(inventory_id=inv_id).exists()
        assert not Inventory.objects.filter(id=inv_id).exists()

    def test_no_hosts(self):
        inv = self._make_inventory_with_hosts(0)
        inv_id = inv.id
        _batched_delete_inventory(inv)
        assert not Inventory.objects.filter(id=inv_id).exists()

    def test_exactly_one_batch(self):
        inv = self._make_inventory_with_hosts(5)
        inv_id = inv.id
        _batched_delete_inventory(inv, batch_size=5)
        assert not Host.objects.filter(inventory_id=inv_id).exists()
        assert not Inventory.objects.filter(id=inv_id).exists()

    def test_idempotent_after_partial_delete(self):
        """Simulate a crash mid-way: delete some hosts manually, then run
        _batched_delete_inventory — it should finish the job cleanly."""
        inv = self._make_inventory_with_hosts(10)
        inv_id = inv.id

        # Simulate a partial deletion (as if the task crashed after 4 hosts)
        partial_pks = list(Host.objects.filter(inventory=inv).values_list('pk', flat=True)[:4])
        Host.objects.filter(pk__in=partial_pks).delete()
        assert Host.objects.filter(inventory_id=inv_id).count() == 6

        # Re-running should delete the remaining hosts and the inventory
        inv.refresh_from_db()
        _batched_delete_inventory(inv, batch_size=3)
        assert not Host.objects.filter(inventory_id=inv_id).exists()
        assert not Inventory.objects.filter(id=inv_id).exists()

    def test_delete_inventory_retries_on_database_error(self):
        """DatabaseError during deletion triggers a retry."""
        from awx.main.tasks.system import delete_inventory

        inv = self._make_inventory_with_hosts(3)
        inv_id = inv.id

        call_count = {'n': 0}
        original = _batched_delete_inventory.__wrapped__ if hasattr(_batched_delete_inventory, '__wrapped__') else _batched_delete_inventory

        def flaky_delete(inventory, batch_size=500):
            call_count['n'] += 1
            if call_count['n'] == 1:
                raise DatabaseError('connection reset')
            return original(inventory, batch_size=batch_size)

        with mock.patch('awx.main.tasks.system._batched_delete_inventory', side_effect=flaky_delete):
            with mock.patch('awx.main.tasks.system.emit_channel_notification'):
                with mock.patch('awx.main.tasks.system.time.sleep'):
                    delete_inventory(inv_id, None, retries=2)

        assert call_count['n'] == 2
        assert not Inventory.objects.filter(id=inv_id).exists()


@pytest.mark.django_db
def test_clear_setting_cache_log_level_branch(settings):
    settings.LOG_AGGREGATOR_LEVEL = 'DEBUG'
    settings.CLUSTER_HOST_ID = 'control-node'
    published_messages = []

    class DummyBroker:
        def publish_message(self, channel, message):
            published_messages.append((channel, message))

        def close(self):
            pass

    dummy_broker = DummyBroker()

    with mock.patch('dispatcherd.control.get_broker', return_value=dummy_broker) as mock_get_broker:
        clear_setting_cache(['LOG_AGGREGATOR_LEVEL'])

    mock_get_broker.assert_called_once()
    assert published_messages, 'control command was not sent through the broker'
    queue, payload = published_messages[-1]
    assert queue == 'control-node'
    body = json.loads(payload)
    assert body['control'] == 'set_log_level'
    assert body['control_data'] == {'level': 'DEBUG'}


@pytest.mark.django_db
def test_configure_dispatcher_logging_updates_level(settings):
    original_logging_settings = copy.deepcopy(settings.LOGGING)
    settings.LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'dynamic_level_filter': {
                '()': 'logging.Filter',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'filters': ['dynamic_level_filter'],
                'stream': 'ext://sys.stdout',
            }
        },
        'loggers': {
            'dispatcherd': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            }
        },
    }
    settings.LOG_AGGREGATOR_LEVEL = 'WARNING'

    Command().configure_dispatcher_logging()

    assert logging.getLogger('dispatcherd').level == logging.WARNING
    settings.LOGGING = original_logging_settings


# ── Helpers ───────────────────────────────────────────────────────────────────

_UNSET = object()


def _mesh_status(known_costs=_UNSET, advertisements=_UNSET):
    return {
        'KnownConnectionCosts': {} if known_costs is _UNSET else known_costs,
        'Advertisements': [] if advertisements is _UNSET else [{'NodeID': n} for n in (advertisements or [])],
    }


def _make_lock(acquired):
    @contextmanager
    def _cm(name, wait=True, **kwargs):
        yield acquired

    return _cm


def _make_lock_sequence(sequence):
    it = iter(sequence)

    @contextmanager
    def _cm(name, wait=True, **kwargs):
        yield next(it)

    return _cm


# ── Tests: _mesh_all_ready_nodes_visible ──────────────────────────────────────


@pytest.mark.django_db
class TestMeshAllReadyNodesVisible:
    """Gate uses KnownConnectionCosts (receptor routing table) as the stability signal.

    No DB state is consulted — KnownConnectionCosts is maintained entirely by
    receptor's routing protocol. Empty table = routing not yet established (Window A).
    """

    def test_defers_when_routing_table_empty(self):
        status = _mesh_status(known_costs={})
        assert _mesh_all_ready_nodes_visible(status) is False

    def test_defers_when_routing_table_null(self):
        """Receptor is a Go service; nil map marshals to JSON null → Python None."""
        status = _mesh_status(known_costs=None)
        assert _mesh_all_ready_nodes_visible(status) is False

    def test_passes_when_routing_established(self):
        status = _mesh_status(known_costs={'ctrl-0': {'ee-0': 1}})
        assert _mesh_all_ready_nodes_visible(status) is True

    def test_passes_when_routing_established_dead_ee_not_in_routing(self):
        """Gate checks only whether routing exists, not which nodes appear."""
        status = _mesh_status(known_costs={'ctrl-0': {'live-ee': 1}})
        assert _mesh_all_ready_nodes_visible(status) is True

    def test_fails_open_when_mesh_status_none(self):
        """Fail open so existing peer-judgment error paths are not bypassed."""
        assert _mesh_all_ready_nodes_visible(None) is True


# ── Tests: _heartbeat_handle_lost_instances (task manager lock) ───────────────


@pytest.mark.django_db
class TestHeartbeatHandleLostInstancesLock:
    def _run(self, lost_instances, lock_behavior):
        with (
            mock.patch('awx.main.tasks.system.reaper'),
            mock.patch('awx.main.tasks.system.advisory_lock', lock_behavior),
        ):
            _heartbeat_handle_lost_instances(lost_instances, None)

    def test_processes_instance_when_lock_acquired(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='ready')
        self._run([inst], _make_lock(True))
        inst.refresh_from_db()
        assert inst.node_state == Instance.States.UNAVAILABLE

    def test_skips_instance_when_lock_unavailable(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='ready')
        self._run([inst], _make_lock(False))
        inst.refresh_from_db()
        assert inst.node_state == Instance.States.READY

    def test_logs_when_instance_deferred(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='ready')
        with (
            mock.patch('awx.main.tasks.system.reaper'),
            mock.patch('awx.main.tasks.system.advisory_lock', _make_lock(False)),
            mock.patch('awx.main.tasks.system.logger') as mock_log,
        ):
            _heartbeat_handle_lost_instances([inst], None)
        assert mock_log.info.called
        assert 'ctrl-1' in mock_log.info.call_args[0][0]

    def test_per_instance_lock_first_skipped_second_processed(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst1 = Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='ready')
        inst2 = Instance.objects.create(hostname='ctrl-2', node_type='control', node_state='ready')
        self._run([inst1, inst2], _make_lock_sequence([False, True]))
        inst1.refresh_from_db()
        inst2.refresh_from_db()
        assert inst1.node_state == Instance.States.READY
        assert inst2.node_state == Instance.States.UNAVAILABLE

    def test_all_instances_processed_when_lock_always_acquired(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst1 = Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='ready')
        inst2 = Instance.objects.create(hostname='ctrl-2', node_type='control', node_state='ready')
        self._run([inst1, inst2], _make_lock(True))
        inst1.refresh_from_db()
        inst2.refresh_from_db()
        assert inst1.node_state == Instance.States.UNAVAILABLE
        assert inst2.node_state == Instance.States.UNAVAILABLE


# ── Tests: _reap_and_mark_lost_instance (exception / branch coverage) ────────


@pytest.mark.django_db
class TestReapAndMarkLostInstance:
    def _inst(self, **kwargs):
        defaults = {'hostname': 'ctrl-1', 'node_type': 'control', 'node_state': 'ready'}
        defaults.update(kwargs)
        return Instance.objects.create(**defaults)

    def test_reap_exception_does_not_prevent_mark_offline(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst()
        Job.objects.create(controller_node=inst.hostname, status='running', work_unit_id=None)
        with mock.patch('awx.main.tasks.system.reaper') as mock_reaper:
            mock_reaper.reap_job.side_effect = Exception('receptor timeout')
            _reap_and_mark_lost_instance(inst)
        inst.refresh_from_db()
        assert inst.node_state == Instance.States.UNAVAILABLE

    def test_auto_deprovision_deletes_control_node(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = True
        inst = self._inst(hostname='ctrl-dep')
        with mock.patch('awx.main.tasks.system.reaper'):
            _reap_and_mark_lost_instance(inst)
        assert not Instance.objects.filter(hostname='ctrl-dep').exists()

    def test_skips_mark_offline_when_node_already_unavailable(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst(node_state='unavailable')
        with mock.patch('awx.main.tasks.system.reaper'):
            _reap_and_mark_lost_instance(inst)
        inst.refresh_from_db()
        assert inst.node_state == Instance.States.UNAVAILABLE

    def test_database_error_without_sqlstate_logs_exception(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst()
        err = DatabaseError('constraint violation')
        err.__cause__ = None
        with (
            mock.patch('awx.main.tasks.system.reaper'),
            mock.patch.object(inst, 'mark_offline', side_effect=err),
            mock.patch('awx.main.tasks.system.logger') as mock_log,
        ):
            _reap_and_mark_lost_instance(inst)
        assert mock_log.exception.called
        assert 'No SQL state' in mock_log.exception.call_args[0][0]

    def test_database_error_with_sqlstate_logs_details(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst()
        err = DatabaseError('unique violation')

        class _FakePsycopgError(Exception):
            sqlstate = 'some_state'

        err.__cause__ = _FakePsycopgError('underlying pg error')
        with (
            mock.patch('awx.main.tasks.system.reaper'),
            mock.patch.object(inst, 'mark_offline', side_effect=err),
            mock.patch('awx.main.tasks.system.logger') as mock_log,
            mock.patch('awx.main.tasks.system.psycopg') as mock_psycopg,
        ):
            mock_psycopg.errors.lookup.return_value = 'SomeError'
            mock_psycopg.errors.NoData = 'other_state'
            _reap_and_mark_lost_instance(inst)
        mock_psycopg.errors.lookup.assert_called_once_with('some_state')
        assert mock_log.exception.called

    def test_database_error_with_nodata_sqlstate_logs_debug(self, settings):
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst()
        err = DatabaseError('nodata')

        class _FakePsycopgError(Exception):
            sqlstate = 'nodata_state'

        err.__cause__ = _FakePsycopgError('nodata cause')
        with (
            mock.patch('awx.main.tasks.system.reaper'),
            mock.patch.object(inst, 'mark_offline', side_effect=err),
            mock.patch('awx.main.tasks.system.logger') as mock_log,
            mock.patch('awx.main.tasks.system.psycopg') as mock_psycopg,
        ):
            mock_psycopg.errors.lookup.return_value = 'NoData'
            mock_psycopg.errors.NoData = 'nodata_state'
            _reap_and_mark_lost_instance(inst)
        mock_log.exception.assert_not_called()
        debug_messages = [str(call) for call in mock_log.debug.call_args_list]
        assert any('marked' in m for m in debug_messages)


# ── Tests: inspect_execution_and_hop_nodes ────────────────────────────────────


@pytest.mark.django_db
class TestInspectExecutionAndHopNodes:
    @mock.patch('awx.main.tasks.system.inspect_established_receptor_connections')
    def test_skips_when_lock_not_acquired(self, mock_inspect_conns):
        with mock.patch('awx.main.tasks.system.advisory_lock', _make_lock(False)):
            inspect_execution_and_hop_nodes([], _mesh_status())
        mock_inspect_conns.assert_not_called()

    @mock.patch('awx.main.tasks.system.inspect_established_receptor_connections')
    def test_skips_when_mesh_status_none(self, mock_inspect_conns):
        with mock.patch('awx.main.tasks.system.advisory_lock', _make_lock(True)):
            inspect_execution_and_hop_nodes([], None)
        mock_inspect_conns.assert_not_called()

    @mock.patch('awx.main.tasks.system.inspect_established_receptor_connections')
    def test_runs_when_lock_acquired(self, mock_inspect_conns):
        with mock.patch('awx.main.tasks.system.advisory_lock', _make_lock(True)):
            inspect_execution_and_hop_nodes([], _mesh_status())
        mock_inspect_conns.assert_called_once()

    @mock.patch('awx.main.tasks.system.inspect_established_receptor_connections')
    def test_updates_last_seen_for_execution_nodes(self, mock_inspect_conns):
        exec_node = Instance.objects.create(hostname='exec-1', node_type='execution', node_state='ready')
        control_node = Instance.objects.create(hostname='control-1', node_type='control', node_state='ready')
        status = {
            'KnownConnectionCosts': {},
            'Advertisements': [
                {'NodeID': 'exec-1', 'Time': '2026-01-01T00:00:00+00:00'},
                {'NodeID': 'control-1', 'Time': '2026-01-01T00:00:00+00:00'},
            ],
        }
        with mock.patch('awx.main.tasks.system.advisory_lock', _make_lock(True)):
            inspect_execution_and_hop_nodes([exec_node, control_node], status)
        exec_node.refresh_from_db()
        assert exec_node.last_seen is not None  # was None; function set it from Advertisements Time
        control_node.refresh_from_db()
        assert control_node.last_seen is None  # control nodes not updated by this function


# ── Integration tests: _heartbeat_instance_management ────────────────────────


@pytest.mark.django_db
def test_heartbeat_defers_lost_instances_when_mesh_gate_blocks(settings):
    """Gate returns False (empty KnownConnectionCosts) → lost_instances suppressed."""
    settings.CLUSTER_HOST_ID = 'ctrl-0'
    settings.AWX_AUTO_DEPROVISION_INSTANCES = False
    settings.CLUSTER_NODE_HEARTBEAT_PERIOD = 60
    settings.CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE = 2

    this_inst = Instance.objects.create(hostname='ctrl-0', node_type='control', node_state='ready')
    this_inst.last_seen = now() - timedelta(seconds=30)
    this_inst.save(update_fields=['last_seen'])

    lost_peer = Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='ready')
    lost_peer.last_seen = now() - timedelta(seconds=200)  # > 120s grace → is_lost() True
    lost_peer.save(update_fields=['last_seen'])

    mock_ctl = mock.MagicMock()
    mock_ctl.simple_command.return_value = {'KnownConnectionCosts': {}, 'Advertisements': []}

    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl),
        mock.patch('awx.main.tasks.system.inspect_execution_and_hop_nodes'),
        mock.patch.object(Instance, 'local_health_check'),
    ):
        _, _, lost_result, _ = _heartbeat_instance_management()

    assert lost_result == []


@pytest.mark.django_db
def test_heartbeat_marks_offline_when_receptor_unavailable(settings):
    """FileNotFoundError from get_receptor_ctl → this_inst marked offline, returns (None, None, None, None)."""
    settings.CLUSTER_HOST_ID = 'ctrl-0'
    settings.AWX_AUTO_DEPROVISION_INSTANCES = False

    this_inst = Instance.objects.create(hostname='ctrl-0', node_type='control', node_state='ready')
    this_inst.last_seen = now() - timedelta(seconds=30)
    this_inst.save(update_fields=['last_seen'])

    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl', side_effect=FileNotFoundError),
        mock.patch.object(Instance, 'local_health_check'),
    ):
        result = _heartbeat_instance_management()

    assert result == (None, None, None, None)
    this_inst.refresh_from_db()
    assert this_inst.node_state == Instance.States.UNAVAILABLE


# ── AAP-89607: unified startup job processing ─────────────────────────────────


@pytest.mark.django_db
def test_process_startup_jobs_skips_dispatched_job(me_inst, settings):
    """_process_startup_jobs() must not reap jobs that have a work_unit_id (dispatched to receptor).

    Dispatched jobs may still be running on the EE; the adoption path will reconnect to them.
    """
    dispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='abc12345')
    ctl = MagicMock()
    with patch('awx.main.tasks.receptor.reattach_to_work_unit', return_value=False):
        _process_startup_jobs(me_inst, ctl)
    dispatched.refresh_from_db()
    assert dispatched.status == 'running', 'dispatched job was wrongly reaped by _process_startup_jobs()'


@pytest.mark.django_db
def test_process_startup_jobs_reaps_undispatched_job(me_inst, settings):
    """_process_startup_jobs() reaps jobs with no work_unit_id (never dispatched to receptor)."""
    undispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=None)
    ctl = MagicMock()
    _process_startup_jobs(me_inst, ctl)
    undispatched.refresh_from_db()
    assert undispatched.status == 'failed', 'undispatched job should have been reaped'


@pytest.mark.django_db
def test_reap_reaps_dispatched_jobs(me_inst):
    """reap() reaps dispatched jobs (no undispatched_only filter)."""
    dispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-xyz')
    reap(instance=me_inst)
    dispatched.refresh_from_db()
    assert dispatched.status == 'failed', 'reap() should reap dispatched jobs'


# ── AAP-89607: adoption loop ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_startup_no_op_when_no_jobs(me_inst):
    """_process_startup_jobs() is a no-op when there are no running jobs."""
    ctl = MagicMock()
    _process_startup_jobs(me_inst, ctl)
    ctl.simple_command.assert_not_called()


@pytest.mark.django_db
def test_adoption_skips_still_running_work_unit(me_inst):
    """Startup adoption defers a job whose receptor work unit is still running."""
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='running-unit')
    ctl = MagicMock()
    ctl.simple_command.return_value = {'StateName': 'Running', 'ExitCode': None}

    with patch('awx.main.tasks.receptor.reattach_to_work_unit', wraps=lambda j, c: False):
        _process_startup_jobs(me_inst, ctl)

    job.refresh_from_db()
    assert job.status == 'running', 'job should still be running — adoption deferred'


@pytest.mark.django_db
def test_adoption_timeout_fails_job(me_inst, settings):
    """Jobs orphaned longer than HADR_JOB_ADOPTION_TIMEOUT are failed.

    Timeout is measured from the last event received (orphaned_since), not from job.started.
    With no events in DB the fallback is job.started — that's what this test exercises.
    """
    from django.utils.timezone import now, timedelta

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id='old-unit',
        started=now() - timedelta(seconds=7200),  # started 2h ago, no events in DB → orphaned 2h
    )
    ctl = MagicMock()
    _process_startup_jobs(me_inst, ctl)
    job.refresh_from_db()
    assert job.status == 'failed', 'timed-out job should be reaped by startup job processing'
    assert 'HADR_JOB_ADOPTION_TIMEOUT' in job.job_explanation


@pytest.mark.django_db
def test_adoption_timeout_spares_long_running_job_with_recent_events(me_inst, settings):
    """Long-running jobs are NOT killed if events arrived recently.

    A job started 2 hours ago but with events arriving 5 minutes ago (controller just
    restarted briefly) should NOT be failed — the outage was short, not the job runtime.
    This is the fix for the job.started bug: we measure from last_event.created, not
    from job.started.
    """
    from django.utils.timezone import now, timedelta
    from awx.main.models import JobEvent

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id='long-running-unit',
        started=now() - timedelta(seconds=7200),  # started 2h ago → old job.started
    )
    # Simulate events arriving 5 minutes ago (brief controller outage)
    JobEvent.objects.create(
        job=job,
        counter=10,
        event='runner_on_ok',
        job_created=job.created,
    )
    # Manually set created to 5 min ago (default is now())
    JobEvent.objects.filter(job=job).update(created=now() - timedelta(seconds=300))

    ctl = MagicMock()
    _process_startup_jobs(me_inst, ctl)
    job.refresh_from_db()
    assert job.status == 'running', 'Long-running job with recent events must not be failed — measure timeout from last event, not job.started'


@pytest.mark.django_db
def test_adoption_finalizes_successful_job(me_inst):
    """reattach_to_work_unit finalizes a job as successful when ExitCode=0."""
    from awx.main.tasks.receptor import reattach_to_work_unit

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='done-unit')
    ctl = MagicMock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0}

    with (
        patch('awx.main.tasks.receptor.AWXReceptorJob') as mock_job_cls,
        patch('awx.main.tasks.callback.RunnerCallback'),
    ):
        mock_instance = MagicMock()
        mock_instance._process_phase.return_value = MagicMock()
        mock_job_cls.return_value = mock_instance

        reattach_to_work_unit(job, ctl)

    job.refresh_from_db()
    assert job.status == 'successful'


@pytest.mark.django_db
def test_adoption_finalizes_failed_job(me_inst):
    """reattach_to_work_unit finalizes a job as failed when ExitCode=1."""
    from awx.main.tasks.receptor import reattach_to_work_unit

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='failed-unit')
    ctl = MagicMock()
    ctl.simple_command.return_value = {'StateName': 'Failed', 'ExitCode': 1}

    with (
        patch('awx.main.tasks.receptor.AWXReceptorJob') as mock_job_cls,
        patch('awx.main.tasks.callback.RunnerCallback'),
    ):
        mock_instance = MagicMock()
        mock_instance._process_phase.return_value = MagicMock(status='failed', rc=1)
        mock_job_cls.return_value = mock_instance

        reattach_to_work_unit(job, ctl)

    job.refresh_from_db()
    assert job.status == 'failed'


@pytest.mark.django_db
def test_process_running_jobs_adopts_dispatched_skips_active(me_inst):
    """_process_running_jobs() adopts dispatched orphaned jobs and leaves active ones alone."""
    active_job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='active-unit', celery_task_id='active-uuid')
    orphaned_dispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='orphaned-unit', celery_task_id='orphan-uuid')
    ctl = MagicMock()

    adopted = []
    with patch('awx.main.tasks.receptor.reattach_to_work_unit', side_effect=lambda j, c: adopted.append(j.id)):
        _process_running_jobs(me_inst, ctl, active_task_ids={'active-uuid'}, ref_time=None)

    assert orphaned_dispatched.id in adopted, 'orphaned dispatched job should be adopted'
    assert active_job.id not in adopted, 'active job should not be touched'


@pytest.mark.django_db
def test_process_running_jobs_reaps_undispatched(me_inst):
    """_process_running_jobs() reaps undispatched orphaned jobs."""
    undispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=None, celery_task_id='orphan-undispatched')
    ctl = MagicMock()
    _process_running_jobs(me_inst, ctl, active_task_ids=set(), ref_time=None)
    undispatched.refresh_from_db()
    assert undispatched.status == 'failed', 'undispatched orphaned job should be reaped'


@pytest.mark.django_db
def test_startup_reap_undispatched_reaps_undispatched_leaves_dispatched(me_inst):
    """_startup_reap_undispatched() reaps jobs with no work_unit_id, leaves dispatched jobs alone.

    This is the unconditional safety net called from _run_dispatch_startup_common for cases
    where cluster_node_heartbeat returns early (receptor unavailable, rejoining cluster).
    """
    undispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=None)
    dispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='abc-unit')
    _startup_reap_undispatched(me_inst.hostname)
    undispatched.refresh_from_db()
    dispatched.refresh_from_db()
    assert undispatched.status == 'failed', 'undispatched job should be reaped by safety net'
    assert dispatched.status == 'running', 'dispatched job must not be reaped (adoption loop handles it)'


@pytest.mark.django_db
def test_startup_reap_undispatched_no_op_when_no_jobs(me_inst):
    """_startup_reap_undispatched() is a no-op when no undispatched running jobs exist."""
    _startup_reap_undispatched(me_inst.hostname)  # should not raise


@pytest.mark.django_db
def test_startup_reap_undispatched_skips_workflow_jobs(me_inst):
    """_startup_reap_undispatched() must not reap WorkflowJobs.

    WorkflowJob has work_unit_id=None (it never owns a receptor work unit) but must not
    be reaped on controller restart — it coordinates via its node jobs, not receptor directly.
    """
    wfj = WorkflowJob.objects.create(status='running', controller_node=me_inst.hostname)
    _startup_reap_undispatched(me_inst.hostname)
    wfj.refresh_from_db()
    assert wfj.status == 'running', 'WorkflowJob must not be reaped by startup safety net'


@pytest.mark.django_db
def test_process_startup_jobs_skips_workflow_jobs(me_inst, settings):
    """_process_startup_jobs() must not reap WorkflowJobs on controller restart.

    WorkflowJob has work_unit_id=None but is not a receptor-dispatched job; reaping it
    on startup would immediately fail running workflows.
    """
    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    wfj = WorkflowJob.objects.create(status='running', controller_node=me_inst.hostname)
    ctl = MagicMock()
    _process_startup_jobs(me_inst, ctl)
    wfj.refresh_from_db()
    assert wfj.status == 'running', 'WorkflowJob must not be reaped by startup job loop'


@pytest.mark.django_db
def test_try_adopt_job_timeout_reaps(me_inst):
    """_try_adopt_job reaps a job orphaned longer than HADR_JOB_ADOPTION_TIMEOUT."""
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id='stale-unit',
        started=now() - timedelta(seconds=7200),
    )
    ctl = MagicMock()
    timeout_cutoff = now() - timedelta(seconds=3600)
    with patch('awx.main.tasks.receptor.reattach_to_work_unit') as mock_reattach:
        _try_adopt_job(job, ctl, 3600, timeout_cutoff)
    mock_reattach.assert_not_called()
    job.refresh_from_db()
    assert job.status == 'failed', 'timed-out orphaned job should be reaped'


@pytest.mark.django_db
def test_try_adopt_job_exception_is_swallowed(me_inst):
    """_try_adopt_job swallows exceptions from reattach_to_work_unit and does not re-raise."""
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-err')
    ctl = MagicMock()
    timeout_cutoff = now() - timedelta(seconds=3600)
    with patch('awx.main.tasks.receptor.reattach_to_work_unit', side_effect=RuntimeError('network failure')):
        _try_adopt_job(job, ctl, 3600, timeout_cutoff)  # must not raise


@pytest.mark.django_db
def test_adoption_counter_skip_dedup():
    """RunnerCallback.event_handler skips events whose counter is in persisted_counters.

    Uses a set rather than a max threshold so out-of-order worker persistence doesn't
    cause gaps: a higher-counter event committed while a lower-counter event is still
    buffered would erroneously skip the lower event with a max-based approach.
    """
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback()
    cb.persisted_counters = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}

    dispatched = []
    cb.dispatcher = MagicMock()
    cb.dispatcher.dispatch.side_effect = dispatched.append

    # mock the minimum needed for event_handler to run
    from collections import deque

    cb.instance = MagicMock()
    cb.instance.event_class.WRAPUP_EVENT = 'playbook_on_stats'
    cb.event_data_key = 'job_id'
    cb.job_created = None
    cb.parent_workflow_job_id = None
    cb.host_map = {}
    cb.recent_event_timings = deque(maxlen=100)

    # event whose counter is in the persisted set — should be skipped
    cb.event_handler({'event': 'runner_on_ok', 'counter': 5, 'job_id': 1})
    assert len(dispatched) == 0, 'event with counter in persisted_counters should be skipped'

    # event at the top of the set — also skipped
    cb.event_handler({'event': 'runner_on_ok', 'counter': 10, 'job_id': 1})
    assert len(dispatched) == 0, 'event at max persisted counter should be skipped'

    # None sentinel disables skip entirely (default RunnerCallback behavior)
    cb.persisted_counters = None
    cb.event_handler({'event': 'runner_on_ok', 'counter': 1, 'job_id': 1})
    # no assertion — just verify no exception; dispatched may or may not be called
    # depending on deeper event_handler logic


# ── reattach_to_work_unit branch coverage ────────────────────────────────────


@pytest.mark.django_db
def test_reattach_receptor_command_fails(me_inst):
    """receptor_ctl.simple_command raising returns False without touching the job."""
    from awx.main.tasks.receptor import reattach_to_work_unit

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-err')
    ctl = MagicMock()
    ctl.simple_command.side_effect = Exception('connection refused')

    result = reattach_to_work_unit(job, ctl)

    assert result is False
    job.refresh_from_db()
    assert job.status == 'running'


@pytest.mark.django_db
def test_reattach_exit_code_from_detail(me_inst):
    """Exit code is parsed from the Detail string when ExitCode is absent."""
    from awx.main.tasks.receptor import reattach_to_work_unit

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-detail')
    ctl = MagicMock()
    ctl.simple_command.return_value = {'StateName': 'Failed', 'Detail': 'exit status 2'}

    with (
        patch('awx.main.tasks.receptor.AWXReceptorJob') as mock_job_cls,
        patch('awx.main.tasks.callback.RunnerCallback'),
    ):
        mock_job_cls.return_value = MagicMock()
        reattach_to_work_unit(job, ctl)

    job.refresh_from_db()
    assert job.status == 'failed'


@pytest.mark.django_db
def test_reattach_exit_code_fallback_succeeded(me_inst):
    """Unparseable Detail with Succeeded state → exit_code=0 → successful."""
    from awx.main.tasks.receptor import reattach_to_work_unit

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-fb-ok')
    ctl = MagicMock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'Detail': 'not-a-number'}

    with (
        patch('awx.main.tasks.receptor.AWXReceptorJob') as mock_job_cls,
        patch('awx.main.tasks.callback.RunnerCallback'),
    ):
        mock_job_cls.return_value = MagicMock()
        reattach_to_work_unit(job, ctl)

    job.refresh_from_db()
    assert job.status == 'successful'


@pytest.mark.django_db
def test_reattach_exit_code_fallback_failed(me_inst):
    """Unparseable Detail with Failed state → exit_code=1 → failed."""
    from awx.main.tasks.receptor import reattach_to_work_unit

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-fb-fail')
    ctl = MagicMock()
    ctl.simple_command.return_value = {'StateName': 'Failed', 'Detail': ''}

    with (
        patch('awx.main.tasks.receptor.AWXReceptorJob') as mock_job_cls,
        patch('awx.main.tasks.callback.RunnerCallback'),
    ):
        mock_job_cls.return_value = MagicMock()
        reattach_to_work_unit(job, ctl)

    job.refresh_from_db()
    assert job.status == 'failed'


@pytest.mark.django_db
def test_reattach_process_phase_raises(me_inst):
    """When _process_phase raises, the job is still finalized via the pre-fetched exit_code."""
    from awx.main.tasks.receptor import reattach_to_work_unit

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-raise')
    ctl = MagicMock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0}

    with (
        patch('awx.main.tasks.receptor.AWXReceptorJob') as mock_job_cls,
        patch('awx.main.tasks.callback.RunnerCallback'),
    ):
        mock_instance = MagicMock()
        mock_instance._process_phase.side_effect = RuntimeError('boom')
        mock_job_cls.return_value = mock_instance
        result = reattach_to_work_unit(job, ctl)

    assert result is True
    job.refresh_from_db()
    assert job.status == 'successful'


@pytest.mark.django_db
def test_reattach_job_already_finalized(me_inst):
    """finished_callback finalizing the job during process phase is not overwritten."""
    from awx.main.tasks.receptor import reattach_to_work_unit

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-already')
    ctl = MagicMock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0}

    def _finalize_in_db(*args, **kwargs):
        Job.objects.filter(pk=job.pk).update(status='successful')

    with (
        patch('awx.main.tasks.receptor.AWXReceptorJob') as mock_job_cls,
        patch('awx.main.tasks.callback.RunnerCallback'),
    ):
        mock_instance = MagicMock()
        mock_instance._process_phase.side_effect = _finalize_in_db
        mock_job_cls.return_value = mock_instance
        reattach_to_work_unit(job, ctl)

    job.refresh_from_db()
    assert job.status == 'successful'
