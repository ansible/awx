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
    adopt_job_async,
)
from awx.main.dispatch.reaper import reap
from awx.main.management.commands.dispatcherd import Command
from django.conf import settings as django_settings
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

    def test_mark_offline_message_stays_translatable_after_queueing_adoption(self, settings):
        """The offline reason must remain lazily translated even on the adoption code path.

        Unpacking apply_async into `_` would rebind the module-level gettext alias for the
        whole function, so the only safe way to keep `_()` working here is to not use `_`
        as the throwaway name.
        """
        from django.utils.functional import Promise
        from unittest.mock import MagicMock

        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst(hostname='ctrl-i18n')
        Job.objects.create(controller_node=inst.hostname, status='running', work_unit_id='unit-i18n', execution_node='remote-ee')

        with (
            mock.patch('awx.main.tasks.system.adopt_job_async') as mock_adopt,
            mock.patch('awx.main.tasks.system.reaper'),
            mock.patch.object(inst, 'mark_offline') as mock_offline,
        ):
            mock_result = MagicMock()
            mock_result.__getitem__.return_value = 'task-uuid'
            mock_adopt.apply_async.return_value = (mock_result, None)
            _reap_and_mark_lost_instance(inst)

        mock_offline.assert_called_once()
        errors = mock_offline.call_args[1]['errors']
        assert isinstance(errors, Promise), f'offline reason is not lazily translated: {errors!r}'
        assert 'unresponsive' in str(errors)

    def test_reap_queues_cross_controller_adoption_for_dispatched_jobs(self, settings):
        """Jobs with work_unit_id are queued for cross-controller adoption, not reaped."""
        from unittest.mock import MagicMock

        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst(hostname='ctrl-lost')
        # Dispatched job (work_unit_id set) — should be adopted, not reaped
        job = Job.objects.create(
            controller_node=inst.hostname,
            status='running',
            work_unit_id='unit-123',
            execution_node='remote-ee',
        )
        with mock.patch('awx.main.tasks.system.adopt_job_async') as mock_adopt, mock.patch('awx.main.tasks.system.reaper') as mock_reaper:
            # Mock apply_async to return (result_dict, None) where result_dict['uuid'] == task-uuid
            mock_result = MagicMock()
            mock_result.__getitem__.return_value = 'task-uuid'
            mock_adopt.apply_async.return_value = (mock_result, None)
            _reap_and_mark_lost_instance(inst)

        # Adoption should be queued, not reaped. Ownership has already moved to us by publish
        # time, so source_controller is CLUSTER_HOST_ID — same kwargs the startup and heartbeat
        # paths publish, which is what on_duplicate='discard' keys on.
        mock_adopt.apply_async.assert_called_once_with(
            args=[job.id], kwargs={'source_controller': settings.CLUSTER_HOST_ID}, queue=mock_adopt.apply_async.call_args[1]['queue']
        )
        mock_reaper.reap_job.assert_not_called()

    def test_reap_claims_ownership_before_publishing_adoption(self, settings):
        """The conditional UPDATE is the mutual-exclusion point, so it has to land before publish."""
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst(hostname='ctrl-lost')
        job = Job.objects.create(controller_node=inst.hostname, status='running', work_unit_id='unit-123', execution_node='remote-ee')

        owner_at_publish = {}

        def _capture(*args, **kwargs):
            owner_at_publish['controller_node'] = Job.objects.get(pk=job.id).controller_node
            return ({'uuid': 'adopt-uuid'}, 'celery')

        with mock.patch('awx.main.tasks.system.adopt_job_async') as mock_adopt, mock.patch('awx.main.tasks.system.reaper'):
            mock_adopt.apply_async = MagicMock(side_effect=_capture)
            _reap_and_mark_lost_instance(inst)

        assert owner_at_publish['controller_node'] == settings.CLUSTER_HOST_ID
        job.refresh_from_db()
        assert job.celery_task_id == 'adopt-uuid'

    def test_reap_skips_adoption_when_another_controller_claimed_first(self, settings):
        """A survivor that loses the conditional UPDATE must neither publish nor reap the job."""
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst(hostname='ctrl-lost')
        job_a = Job.objects.create(
            controller_node=inst.hostname, status='running', work_unit_id='unit-1', execution_node='remote-ee', celery_task_id='untouched'
        )
        job_b = Job.objects.create(
            controller_node=inst.hostname, status='running', work_unit_id='unit-2', execution_node='remote-ee', celery_task_id='untouched'
        )

        def _steal(args=None, **kwargs):
            # Another survivor claims the job we have not reached yet, after our queryset was built
            other = job_b.id if args[0] == job_a.id else job_a.id
            Job.objects.filter(pk=other).update(controller_node='other-survivor')
            return ({'uuid': 'adopt-uuid'}, 'celery')

        with mock.patch('awx.main.tasks.system.adopt_job_async') as mock_adopt, mock.patch('awx.main.tasks.system.reaper') as mock_reaper:
            mock_adopt.apply_async = MagicMock(side_effect=_steal)
            _reap_and_mark_lost_instance(inst)

        assert mock_adopt.apply_async.call_count == 1
        mock_reaper.reap_job.assert_not_called()
        assert Job.objects.filter(controller_node='other-survivor', celery_task_id='untouched').count() == 1
        assert Job.objects.filter(controller_node=settings.CLUSTER_HOST_ID, celery_task_id='adopt-uuid').count() == 1

    def test_reap_does_not_adopt_when_only_execution_node_is_lost(self, settings):
        """A lost EE leaves the job's controller alive and still running it — reap, never adopt."""
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst(hostname='ee-lost', node_type='execution')
        job = Job.objects.create(
            controller_node='live-ctrl',
            status='running',
            work_unit_id='unit-abc',
            execution_node=inst.hostname,
            celery_task_id='original-uuid',
        )
        with mock.patch('awx.main.tasks.system.adopt_job_async') as mock_adopt, mock.patch('awx.main.tasks.system.reaper') as mock_reaper:
            _reap_and_mark_lost_instance(inst)

        mock_adopt.apply_async.assert_not_called()
        mock_reaper.reap_job.assert_called_once()
        # The live controller keeps ownership and its dispatcher task id.
        job.refresh_from_db()
        assert job.controller_node == 'live-ctrl'
        assert job.celery_task_id == 'original-uuid'

    def test_reap_does_not_adopt_when_lost_node_is_both_controller_and_execution_node(self, settings):
        """A lost hybrid node takes its work unit with it — there is nothing left to adopt."""
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst(hostname='hybrid-lost', node_type='hybrid')
        Job.objects.create(
            controller_node=inst.hostname,
            status='running',
            work_unit_id='unit-def',
            execution_node=inst.hostname,
        )
        with mock.patch('awx.main.tasks.system.adopt_job_async') as mock_adopt, mock.patch('awx.main.tasks.system.reaper') as mock_reaper:
            _reap_and_mark_lost_instance(inst)

        mock_adopt.apply_async.assert_not_called()
        mock_reaper.reap_job.assert_called_once()

    def test_reap_reaped_undispatched_jobs_when_lost_instance(self, settings):
        """Jobs without work_unit_id are reaped immediately, not adopted."""
        settings.AWX_AUTO_DEPROVISION_INSTANCES = False
        inst = self._inst(hostname='ctrl-lost')
        # Undispatched job (no work_unit_id) — should be reaped
        Job.objects.create(
            controller_node=inst.hostname,
            status='running',
            work_unit_id=None,
        )
        with mock.patch('awx.main.tasks.system.adopt_job_async') as mock_adopt, mock.patch('awx.main.tasks.system.reaper') as mock_reaper:
            _reap_and_mark_lost_instance(inst)

        # Adoption should NOT be queued
        mock_adopt.apply_async.assert_not_called()
        # Job should be reaped
        mock_reaper.reap_job.assert_called_once()

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


@pytest.mark.parametrize(
    'mesh_status',
    [
        {'KnownConnectionCosts': {}},
        {'Connections': [], 'KnownConnectionCosts': {}, 'RoutingTable': {}},
    ],
)
@pytest.mark.django_db
def test_kubernetes_mesh_gate_allows_empty_routing(settings, mesh_status):
    """In Kubernetes (IS_K8S=True), empty routing is normal — gate passes."""
    settings.IS_K8S = True
    assert _mesh_all_ready_nodes_visible(mesh_status) is True


@pytest.mark.django_db
def test_non_kubernetes_mesh_gate_blocks_empty_routing(settings):
    """Non-Kubernetes deployments block cleanup when routing is empty."""
    settings.IS_K8S = False
    assert _mesh_all_ready_nodes_visible({'KnownConnectionCosts': {}}) is False


@pytest.mark.django_db
def test_kubernetes_passes_mesh_gate_with_empty_routing(settings):
    """In Kubernetes (IS_K8S=True), empty routing is normal — gate passes."""
    settings.CLUSTER_HOST_ID = 'ctrl-0'
    settings.AWX_AUTO_DEPROVISION_INSTANCES = False
    settings.CLUSTER_NODE_HEARTBEAT_PERIOD = 60
    settings.CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE = 2
    settings.IS_K8S = True

    this_inst = Instance.objects.create(hostname='ctrl-0', node_type='control', node_state='ready')
    this_inst.last_seen = now() - timedelta(seconds=30)
    this_inst.save(update_fields=['last_seen'])

    lost_inst = Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='ready')
    lost_inst.last_seen = now() - timedelta(seconds=200)
    lost_inst.save(update_fields=['last_seen'])

    mock_ctl = mock.MagicMock()
    # Empty routing in K8s is expected steady state
    mock_ctl.simple_command.return_value = {'KnownConnectionCosts': {}, 'Advertisements': []}

    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl),
        mock.patch('awx.main.tasks.system.inspect_execution_and_hop_nodes'),
        mock.patch.object(Instance, 'local_health_check'),
    ):
        _, _, lost_result, _ = _heartbeat_instance_management()

    # K8s bypasses the gate — lost instances are reaped even with empty routing
    assert len(lost_result) == 1
    assert lost_result[0].hostname == 'ctrl-1'


@pytest.mark.django_db
def test_mesh_gate_defers_control_but_cleans_execution_hop(settings):
    """When mesh gate blocks cleanup, execution/hop nodes are reaped but control nodes are deferred."""
    settings.CLUSTER_HOST_ID = 'ctrl-0'
    settings.AWX_AUTO_DEPROVISION_INSTANCES = False
    settings.CLUSTER_NODE_HEARTBEAT_PERIOD = 60
    settings.CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE = 2
    settings.IS_K8S = False  # Non-K8s: mesh gate can block

    this_inst = Instance.objects.create(hostname='ctrl-0', node_type='control', node_state='ready')
    this_inst.last_seen = now() - timedelta(seconds=30)
    this_inst.save(update_fields=['last_seen'])

    # Create lost instances of different types
    lost_exec = Instance.objects.create(hostname='exec-1', node_type='execution', node_state='ready')
    lost_exec.last_seen = now() - timedelta(seconds=200)
    lost_exec.save(update_fields=['last_seen'])

    lost_hop = Instance.objects.create(hostname='hop-1', node_type='hop', node_state='ready')
    lost_hop.last_seen = now() - timedelta(seconds=200)
    lost_hop.save(update_fields=['last_seen'])

    lost_ctrl = Instance.objects.create(hostname='ctrl-1', node_type='control', node_state='ready')
    lost_ctrl.last_seen = now() - timedelta(seconds=200)
    lost_ctrl.save(update_fields=['last_seen'])

    mock_ctl = mock.MagicMock()
    # Empty routing — mesh gate will block
    mock_ctl.simple_command.return_value = {'KnownConnectionCosts': {}, 'Advertisements': []}

    with (
        mock.patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl),
        mock.patch('awx.main.tasks.system.inspect_execution_and_hop_nodes'),
        mock.patch.object(Instance, 'local_health_check'),
    ):
        _, _, lost_result, _ = _heartbeat_instance_management()

    # Execution and hop nodes should be in lost_result (reaped immediately)
    # Control node should be deferred (not in lost_result)
    hostnames = [inst.hostname for inst in lost_result]
    assert 'exec-1' in hostnames, 'Execution node should be in lost list even when mesh gate blocks'
    assert 'hop-1' in hostnames, 'Hop node should be in lost list even when mesh gate blocks'
    assert 'ctrl-1' not in hostnames, 'Control node should be deferred when mesh gate blocks'


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

    Dispatched jobs are handed to adopt_job_async for background streaming adoption.
    """
    dispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='abc12345')
    with patch('awx.main.tasks.system.adopt_job_async') as mock_adopt:
        mock_adopt.apply_async = MagicMock(return_value=({'uuid': 'adopt-uuid'}, 'celery'))
        _process_startup_jobs(me_inst)
    dispatched.refresh_from_db()
    assert dispatched.status == 'running', 'dispatched job was wrongly reaped by _process_startup_jobs()'
    mock_adopt.apply_async.assert_called_once()


@pytest.mark.django_db
def test_process_startup_jobs_persists_adoption_task_id(me_inst):
    """celery_task_id must point at the adoption task, otherwise the next heartbeat re-queues it."""
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-1', celery_task_id='original-dispatch-uuid')
    with patch('awx.main.tasks.system.adopt_job_async') as mock_adopt:
        mock_adopt.apply_async = MagicMock(return_value=({'uuid': 'adopt-uuid'}, 'celery'))
        _process_startup_jobs(me_inst)
    job.refresh_from_db()
    assert job.celery_task_id == 'adopt-uuid'


@pytest.mark.django_db
def test_process_running_jobs_persists_adoption_task_id(me_inst):
    """Same as startup: without this the job looks orphaned forever and is re-queued every heartbeat."""
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-1', celery_task_id='stale-uuid')
    with patch('awx.main.tasks.system.adopt_job_async') as mock_adopt:
        mock_adopt.apply_async = MagicMock(return_value=({'uuid': 'adopt-uuid'}, 'celery'))
        _process_running_jobs(me_inst, active_task_ids={'some-other-uuid'}, ref_time=None)
    job.refresh_from_db()
    assert job.celery_task_id == 'adopt-uuid'


@pytest.mark.django_db
def test_process_startup_jobs_reaps_undispatched_job(me_inst, settings):
    """_process_startup_jobs() reaps jobs with no work_unit_id (never dispatched to receptor)."""
    undispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=None)
    _process_startup_jobs(me_inst)
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
    with patch('awx.main.tasks.system.adopt_job_async') as mock_adopt:
        mock_adopt.apply_async = MagicMock()
        _process_startup_jobs(me_inst)
    mock_adopt.apply_async.assert_not_called()


@pytest.mark.django_db
def test_adoption_skips_still_running_work_unit(me_inst):
    """Startup dispatches adopt_job_async for a still-running job — no inline blocking."""
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='running-unit')

    with patch('awx.main.tasks.system.adopt_job_async') as mock_adopt:
        mock_adopt.apply_async = MagicMock()
        _process_startup_jobs(me_inst)

    mock_adopt.apply_async.assert_called_once_with(
        args=[job.id], kwargs={'source_controller': me_inst.hostname}, queue=mock_adopt.apply_async.call_args[1]['queue']
    )
    job.refresh_from_db()
    assert job.status == 'running', 'job must not be reaped — adoption deferred to background task'


@pytest.mark.django_db
def test_adoption_timeout_fails_job(me_inst, settings):
    """Jobs orphaned longer than HADR_JOB_ADOPTION_TIMEOUT are reaped if status query fails.

    Timeout is measured from the last event received, not from job.started.
    Unit status must be unreachable (query fails) to trigger timeout.
    """
    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    from awx.main.tasks.system import adopt_job_async

    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id='old-unit',
        started=now() - timedelta(seconds=7200),
    )
    mock_ctl = MagicMock()
    # Status query fails (network error, unit unreachable)
    # This is the ONLY case where timeout should trigger
    mock_ctl.simple_command.side_effect = RuntimeError('work unit unreachable')
    with patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl), patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach:
        adopt_job_async(job.id, source_controller=me_inst.hostname)
    mock_reattach.assert_not_called()
    job.refresh_from_db()
    assert job.status == 'failed', 'timed-out job should be reaped by adopt_job_async'
    assert 'HADR_JOB_ADOPTION_TIMEOUT' in job.job_explanation


@pytest.mark.django_db
def test_adoption_timeout_spares_long_running_job_with_recent_events(me_inst, settings):
    """Long-running jobs are NOT killed if events arrived recently.

    A job started 2 hours ago but with events 5 minutes ago (brief outage) must not be failed.
    Timeout is measured from last_event.created, not job.started.
    """
    from awx.main.models import JobEvent
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id='long-running-unit',
        started=now() - timedelta(seconds=7200),
    )
    JobEvent.objects.create(job=job, counter=10, event='runner_on_ok', job_created=job.created)
    JobEvent.objects.filter(job=job).update(created=now() - timedelta(seconds=300))

    with patch('awx.main.tasks.system.get_receptor_ctl'), patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach:
        adopt_job_async(job.id, source_controller=me_inst.hostname)
    mock_reattach.assert_called_once()
    job.refresh_from_db()
    assert job.status == 'running', 'Long-running job with recent events must not be failed'


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
        mock_instance._process_phase.return_value = MagicMock(status='successful', rc=0)
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
    """_process_running_jobs() dispatches adopt_job_async for orphaned jobs, skips active ones."""
    active_job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='active-unit', celery_task_id='active-uuid')
    orphaned_dispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='orphaned-unit', celery_task_id='orphan-uuid')

    dispatched_ids = []

    def _record(args, **kw):
        dispatched_ids.append(args[0])
        return ({'uuid': f'adopt-{args[0]}'}, 'celery')

    with patch('awx.main.tasks.system.adopt_job_async') as mock_adopt:
        mock_adopt.apply_async = MagicMock(side_effect=_record)
        _process_running_jobs(me_inst, active_task_ids={'active-uuid'}, ref_time=None)

    assert orphaned_dispatched.id in dispatched_ids, 'orphaned dispatched job should be queued for adoption'
    assert active_job.id not in dispatched_ids, 'active job should not be touched'


@pytest.mark.django_db
def test_process_running_jobs_reaps_undispatched(me_inst):
    """_process_running_jobs() reaps undispatched orphaned jobs."""
    undispatched = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=None, celery_task_id='orphan-undispatched')
    _process_running_jobs(me_inst, active_task_ids=set(), ref_time=None)
    undispatched.refresh_from_db()
    assert undispatched.status == 'failed', 'undispatched orphaned job should be reaped'


@pytest.mark.django_db
def test_process_running_jobs_noop_when_no_orphaned_jobs(me_inst):
    """_process_running_jobs() is a no-op (early return) when all running jobs are active."""
    active_job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='u1', celery_task_id='active-uuid')
    with patch('awx.main.tasks.system.adopt_job_async') as mock_adopt:
        mock_adopt.apply_async = MagicMock()
        _process_running_jobs(me_inst, active_task_ids={'active-uuid'}, ref_time=None)
    mock_adopt.apply_async.assert_not_called()
    active_job.refresh_from_db()
    assert active_job.status == 'running'


@pytest.mark.django_db
def test_process_running_jobs_ref_time_filter(me_inst):
    """_process_running_jobs() excludes jobs started after ref_time."""
    future_job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id=None,
        celery_task_id='future-uuid',
        started=now() + timedelta(seconds=60),
    )
    ref_time = now()
    with patch('awx.main.tasks.system.adopt_job_async') as mock_adopt:
        mock_adopt.apply_async = MagicMock()
        _process_running_jobs(me_inst, active_task_ids=set(), ref_time=ref_time)
    mock_adopt.apply_async.assert_not_called()
    future_job.refresh_from_db()
    assert future_job.status == 'running', 'job started after ref_time should not be touched'


@pytest.mark.django_db
def test_process_running_jobs_exception_does_not_abort_loop(me_inst):
    """Exception in _process_running_jobs job loop is caught — remaining jobs still processed."""
    job1 = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-a', celery_task_id='uuid-a')
    job2 = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-b', celery_task_id='uuid-b')

    dispatched = []

    def side_effect(args, **kw):
        if args[0] == job1.id:
            raise RuntimeError('simulated failure')
        dispatched.append(args[0])

    with patch('awx.main.tasks.system.adopt_job_async') as mock_adopt:
        mock_adopt.apply_async = MagicMock(side_effect=side_effect)
        _process_running_jobs(me_inst, active_task_ids=set(), ref_time=None)

    assert job2.id in dispatched, 'second job must be processed even though first raised'


@pytest.mark.django_db
def test_process_startup_jobs_exception_does_not_abort_loop(me_inst, settings):
    """Exception in _process_startup_jobs job loop is caught — remaining jobs still processed."""
    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job1 = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-err')
    job2 = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id=None)

    def side_effect(args, **kw):
        if args[0] == job1.id:
            raise RuntimeError('simulated failure')

    with patch('awx.main.tasks.system.adopt_job_async') as mock_adopt:
        mock_adopt.apply_async = MagicMock(side_effect=side_effect)
        _process_startup_jobs(me_inst)

    job2.refresh_from_db()
    assert job2.status == 'failed', 'undispatched job2 must still be reaped after job1 exception'


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
    _process_startup_jobs(me_inst)
    wfj.refresh_from_db()
    assert wfj.status == 'running', 'WorkflowJob must not be reaped by startup job loop'


@pytest.mark.django_db
def test_populate_host_map_from_inventory_resolves_real_hosts(me_inst):
    """Against a real inventory, the adoption path maps host name to the id events are stamped with."""
    from awx.main.tasks.callback import RunnerCallback
    from awx.main.models import Organization, Inventory, Host

    org = Organization.objects.first()
    inv = Inventory.objects.create(name='cb-hostmap-inv', organization=org)
    host = Host.objects.create(name='myhost', inventory=inv)
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-hm', inventory=inv)

    cb = RunnerCallback(model=Job)
    cb.populate_host_map_from_inventory(job)

    assert cb.host_map.get('myhost') == host.id


@pytest.mark.django_db
def test_compute_adoption_dedup_no_events(me_inst):
    """_compute_adoption_dedup returns (0, set()) when job has no events in DB."""
    from awx.main.tasks.receptor import _compute_adoption_dedup

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-1')
    threshold, collision_zone, persisted_ct = _compute_adoption_dedup(job)
    assert threshold == 0
    assert collision_zone == set()
    assert persisted_ct == 0


@pytest.mark.django_db
def test_compute_adoption_dedup_contiguous_events(me_inst):
    """_compute_adoption_dedup returns (max_counter, empty set) for contiguous events."""
    from awx.main.tasks.receptor import _compute_adoption_dedup
    from awx.main.models import JobEvent

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-1')
    for ctr in [1, 2, 3, 4, 5]:
        JobEvent.objects.create(job=job, counter=ctr, event='runner_on_ok', job_created=job.created)

    threshold, collision_zone, persisted_ct = _compute_adoption_dedup(job)
    assert threshold == 5
    assert collision_zone == set()
    assert persisted_ct == 5


@pytest.mark.django_db
def test_compute_adoption_dedup_gap_produces_collision_zone(me_inst):
    """_compute_adoption_dedup finds gap and puts above-gap events in collision_zone.

    Stage 1 detects gap and continues to Stage 2, which loads all counters above safe_threshold.
    For events [1, 2, 3, 5, 6]: gap at 4 sets safe_threshold=3, then collision_zone={5, 6}.
    """
    from awx.main.tasks.receptor import _compute_adoption_dedup
    from awx.main.models import JobEvent

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-1')
    # Events 1-3 contiguous, then gap at 4, then 5 and 6 committed out of order
    for ctr in [1, 2, 3, 5, 6]:
        JobEvent.objects.create(job=job, counter=ctr, event='runner_on_ok', job_created=job.created)

    threshold, collision_zone, persisted_ct = _compute_adoption_dedup(job)
    # Gap detected at 4, safe_threshold stops at 3, collision_zone contains 5 and 6
    assert threshold == 3
    assert collision_zone == {5, 6}
    assert persisted_ct == 5


@pytest.mark.django_db
def test_compute_adoption_dedup_requires_prefix_anchored_at_one(me_inst):
    """A missing counter 1 means nothing is contiguous, so the whole tail is collision zone."""
    from awx.main.tasks.receptor import _compute_adoption_dedup
    from awx.main.models import JobEvent

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-nogap1')
    # Counter 1 never committed; 2-5 did. Treating 5 as contiguous would skip real events.
    for ctr in [2, 3, 4, 5]:
        JobEvent.objects.create(job=job, counter=ctr, event='runner_on_ok', job_created=job.created)

    threshold, collision_zone, persisted_ct = _compute_adoption_dedup(job)
    assert threshold == 0
    assert collision_zone == {2, 3, 4, 5}
    assert persisted_ct == 4


@pytest.mark.django_db
def test_compute_adoption_dedup_counts_events_beyond_the_cap(me_inst, settings, caplog):
    """persisted_ct reflects every persisted event, not just the truncated collision zone.

    event_ct is seeded from this, so using the capped set would undercount exactly when
    truncation happens and leave emitted_events / the EOF final_counter inconsistent.
    """
    from awx.main.tasks.receptor import _compute_adoption_dedup
    from awx.main.models import JobEvent

    settings.JOB_EVENT_WORKERS = 1
    settings.JOB_EVENT_CALLBACK_BUFFER_SIZE = 2  # cap == 2

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-capped')
    # Counter 1 missing, so all five land above safe_threshold and the cap truncates.
    for ctr in [2, 3, 4, 5, 6]:
        JobEvent.objects.create(job=job, counter=ctr, event='runner_on_ok', job_created=job.created)

    with caplog.at_level('WARNING', logger='awx.main.tasks.receptor'):
        threshold, collision_zone, persisted_ct = _compute_adoption_dedup(job)
    # Truncating silently would hide that some replayed events are about to be re-persisted.
    assert 'collision_zone' in caplog.text
    assert threshold == 0
    assert len(collision_zone) == 2
    # Deterministic truncation: keep the counters closest to the contiguous prefix.
    assert collision_zone == {2, 3}
    assert persisted_ct == 5


@pytest.mark.django_db
def test_adopt_job_async_exception_is_swallowed(me_inst, settings):
    """adopt_job_async swallows exceptions from reattach_to_work_unit and does not re-raise."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-err')
    with patch('awx.main.tasks.system.get_receptor_ctl'), patch('awx.main.tasks.system.reattach_to_work_unit', side_effect=RuntimeError('network failure')):
        adopt_job_async(job.id, source_controller=me_inst.hostname)  # must not raise


@pytest.mark.django_db
def test_adoption_counter_skip_dedup():
    """RunnerCallback.event_handler hybrid dedup: O(1) threshold + small collision-zone set.

    safe_threshold skips the contiguous prefix with a single integer comparison.
    persisted_counters (collision_zone) handles out-of-order committed events above
    the threshold — bounded by worker concurrency, not total event count.
    """
    from awx.main.tasks.callback import RunnerCallback

    cb = RunnerCallback()
    # Simulate: events 1-8 committed contiguously (threshold=8),
    # events 9,10 committed out-of-order (collision zone)
    cb.dedup_threshold = 8
    cb.persisted_counters = {9, 10}

    dispatched = []
    cb.dispatcher = MagicMock()
    cb.dispatcher.dispatch.side_effect = dispatched.append

    from collections import deque

    cb.instance = MagicMock()
    cb.instance.event_class.WRAPUP_EVENT = 'playbook_on_stats'
    cb.event_data_key = 'job_id'
    cb.job_created = None
    cb.parent_workflow_job_id = None
    cb.host_map = {}
    cb.recent_event_timings = deque(maxlen=100)

    # below threshold — skipped by O(1) integer check
    cb.event_handler({'event': 'runner_on_ok', 'counter': 5, 'job_id': 1})
    assert len(dispatched) == 0, 'counter <= threshold should be skipped'

    # at threshold — also skipped
    cb.event_handler({'event': 'runner_on_ok', 'counter': 8, 'job_id': 1})
    assert len(dispatched) == 0, 'counter == threshold should be skipped'

    # in collision zone — skipped by set membership
    cb.event_handler({'event': 'runner_on_ok', 'counter': 9, 'job_id': 1})
    assert len(dispatched) == 0, 'counter in collision_zone should be skipped'

    # None threshold disables dedup entirely (normal job path, zero overhead)
    cb.dedup_threshold = None
    cb.persisted_counters = None
    cb.event_handler({'event': 'runner_on_ok', 'counter': 1, 'job_id': 1})
    # no assertion — just verify no exception


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
    """_process_phase returning status='successful' → job finalized as successful."""
    from awx.main.tasks.receptor import reattach_to_work_unit

    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-fb-ok')
    ctl = MagicMock()
    ctl.simple_command.return_value = {'StateName': 'Succeeded', 'Detail': 'not-a-number'}

    with (
        patch('awx.main.tasks.receptor.AWXReceptorJob') as mock_job_cls,
        patch('awx.main.tasks.callback.RunnerCallback'),
    ):
        mock_instance = MagicMock()
        mock_instance._process_phase.return_value = MagicMock(status='successful', rc=0)
        mock_job_cls.return_value = mock_instance
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


@pytest.mark.django_db
def test_adopt_job_async_calls_reattach(me_inst, settings):
    """adopt_job_async creates its own receptor_ctl and calls reattach_to_work_unit with unit_status."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-async')

    with patch('awx.main.tasks.system.get_receptor_ctl') as mock_ctl_factory, patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach:
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    mock_ctl_factory.assert_called_once()
    mock_reattach.assert_called_once()
    # Verify unit_status parameter is passed
    call_args, call_kwargs = mock_reattach.call_args
    assert 'unit_status' in call_kwargs


def _running_adoptions_reply(count):
    """Shape a dispatcherd 'running' reply holding `count` adoption tasks in workers."""
    return [{f'worker-{i}': {'task': 'awx.main.tasks.system.adopt_job_async', 'uuid': f'uuid-{i}'} for i in range(count)}]


def _make_owned_running_jobs(hostname, count):
    """Create `count` running jobs owned by this controller, returning the last one."""
    job = None
    for i in range(count):
        job = Job.objects.create(controller_node=hostname, status='running', work_unit_id=f'unit-slot-{i}')
    return job


@pytest.mark.django_db
def test_adopt_job_async_defers_when_adoption_slots_are_full(me_inst, settings):
    """Adoption holds a dispatcher worker for the job's remaining runtime, so it is capped.

    Over the cap the job is simply not adopted this cycle — the next heartbeat re-queues it,
    because a deferred adoption leaves no running task for _process_running_jobs to exclude.
    """
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    settings.HADR_MAX_CONCURRENT_ADOPTIONS = 1
    settings.CLUSTER_HOST_ID = me_inst.hostname
    job = _make_owned_running_jobs(me_inst.hostname, 3)

    mock_control = MagicMock()
    # Two adoption tasks in workers: this one plus one other, which already fills the cap of 1.
    mock_control.control_with_reply.return_value = _running_adoptions_reply(2)
    with (
        patch('awx.main.tasks.system.get_receptor_ctl'),
        patch('awx.main.tasks.system.get_control_from_settings', return_value=mock_control),
        patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach,
        patch('awx.main.tasks.system.reaper.reap_job') as mock_reap,
    ):
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    mock_control.control_with_reply.assert_called_once()
    mock_reattach.assert_not_called()
    mock_reap.assert_not_called()
    job.refresh_from_db()
    assert job.status == 'running'


@pytest.mark.django_db
def test_adopt_job_async_adopts_when_a_slot_is_free(me_inst, settings):
    """Under the cap, adoption proceeds — only this task's own worker is occupied."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    settings.HADR_MAX_CONCURRENT_ADOPTIONS = 1
    settings.CLUSTER_HOST_ID = me_inst.hostname
    job = _make_owned_running_jobs(me_inst.hostname, 3)

    mock_control = MagicMock()
    mock_control.control_with_reply.return_value = _running_adoptions_reply(1)
    with (
        patch('awx.main.tasks.system.get_receptor_ctl'),
        patch('awx.main.tasks.system.get_control_from_settings', return_value=mock_control),
        patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach,
    ):
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    mock_reattach.assert_called_once()


@pytest.mark.django_db
def test_adopt_job_async_adopts_when_dispatcher_cannot_be_asked(me_inst, settings):
    """The cap fails open: an unadopted job has nothing else to finalize it."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    settings.HADR_MAX_CONCURRENT_ADOPTIONS = 1
    settings.CLUSTER_HOST_ID = me_inst.hostname
    job = _make_owned_running_jobs(me_inst.hostname, 3)

    mock_control = MagicMock()
    mock_control.control_with_reply.side_effect = RuntimeError('no broker')
    with (
        patch('awx.main.tasks.system.get_receptor_ctl'),
        patch('awx.main.tasks.system.get_control_from_settings', return_value=mock_control),
        patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach,
    ):
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    mock_reattach.assert_called_once()


@pytest.mark.django_db
def test_adopt_job_async_skips_slot_query_when_controller_is_quiet(me_inst, settings):
    """The jobs this controller owns bound the adoptions it can have in flight.

    Under that bound the dispatcher is not queried at all, which keeps the common case —
    a controller adopting one or two jobs — free of a control round-trip.
    """
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    settings.HADR_MAX_CONCURRENT_ADOPTIONS = 5
    settings.CLUSTER_HOST_ID = me_inst.hostname
    job = _make_owned_running_jobs(me_inst.hostname, 2)

    with (
        patch('awx.main.tasks.system.get_receptor_ctl'),
        patch('awx.main.tasks.system.get_control_from_settings') as mock_control_factory,
        patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach,
    ):
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    mock_control_factory.assert_not_called()
    mock_reattach.assert_called_once()


@pytest.mark.django_db
def test_adopt_job_async_skips_already_finalized(me_inst, settings):
    """adopt_job_async is a no-op if the job is no longer running."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(controller_node=me_inst.hostname, status='successful', work_unit_id='unit-done')

    with patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach:
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    mock_reattach.assert_not_called()


@pytest.mark.django_db
def test_adopt_job_async_reaps_on_timeout(me_inst, settings):
    """adopt_job_async reaps a job only when status query fails (unit unreachable)."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id='unit-old',
        started=now() - timedelta(seconds=7200),
    )

    mock_ctl = MagicMock()
    # Simulate status lookup failure (network error, unit unreachable)
    # This is the ONLY case where timeout should trigger
    mock_ctl.simple_command.side_effect = RuntimeError('work unit unreachable')
    with (
        patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl),
        patch('awx.main.tasks.system.reaper.reap_job') as mock_reap,
        patch('awx.main.tasks.system.logger') as mock_log,
    ):
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    mock_reap.assert_called_once()
    # The timeout branch returns early — the control socket must still be closed.
    mock_ctl.close.assert_called_once()
    # The cancel is expected to fail on an unreachable unit, so it must not log a traceback.
    mock_log.exception.assert_not_called()
    assert any('Failed to cancel work unit' in call.args[0] for call in mock_log.warning.call_args_list)


@pytest.mark.django_db
def test_adopt_job_async_closes_receptor_ctl_when_reap_raises(me_inst, settings):
    """adopt_job_async closes the control socket even if reaping the timed-out job raises."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id='unit-reap-raises',
        started=now() - timedelta(seconds=7200),
    )

    mock_ctl = MagicMock()
    mock_ctl.simple_command.side_effect = RuntimeError('work unit unreachable')
    with patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl), patch('awx.main.tasks.system.reaper.reap_job') as mock_reap:
        mock_reap.side_effect = RuntimeError('reap failed')
        with pytest.raises(RuntimeError):
            adopt_job_async(job.id, source_controller=me_inst.hostname)

    mock_ctl.close.assert_called_once()


@pytest.mark.django_db
def test_adopt_job_async_accepts_legacy_message_without_source_controller(me_inst, settings):
    """Messages published by a pre-AAP-89602 controller carry args=[job_id] only.

    During a rolling upgrade an older controller can publish into a newer worker's queue,
    so source_controller has to stay optional or that job is dropped with a TypeError.
    """
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    # In a real deployment CLUSTER_HOST_ID is this instance's hostname; the me_inst fixture
    # does not set it, and the legacy default resolves against CLUSTER_HOST_ID.
    settings.CLUSTER_HOST_ID = me_inst.hostname
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-legacy')

    mock_ctl = MagicMock()
    mock_ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0}
    with patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl), patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach:
        adopt_job_async(job.id)

    mock_reattach.assert_called_once()


@pytest.mark.django_db
def test_adopt_job_async_never_reaps_a_reachable_active_unit(me_inst, settings):
    """A reachable Pending/Running unit is never reaped, however long it has been orphaned.

    orphaned_since is only as recent as the last persisted event, and a job that goes an hour
    between events is ordinary — jobs longer than HADR_JOB_ADOPTION_TIMEOUT are ordinary too.
    Reaping on that measure would kill healthy jobs. Only a unit whose status query fails
    times out; a reachable one is handed to reattach, which streams it to completion.
    """
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    for state in ('Pending', 'Running'):
        job = Job.objects.create(
            controller_node=me_inst.hostname,
            status='running',
            work_unit_id=f'unit-longrunning-{state.lower()}',
            started=now() - timedelta(seconds=7200),
        )

        mock_ctl = MagicMock()
        mock_ctl.simple_command.return_value = {'StateName': state}
        with (
            patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl),
            patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach,
            patch('awx.main.tasks.system.reaper.reap_job') as mock_reap,
        ):
            adopt_job_async(job.id, source_controller=me_inst.hostname)

        mock_reap.assert_not_called()
        assert mock_reattach.call_count == 1, f'state {state!r} should be streamed, not reaped'
        mock_ctl.close.assert_called_once()


@pytest.mark.django_db
def test_adopt_job_async_streams_active_unit_within_timeout(me_inst, settings):
    """A Running unit that has not yet exceeded the timeout is handed straight to reattach."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id='unit-running-fresh',
        started=now() - timedelta(seconds=60),
    )

    mock_ctl = MagicMock()
    mock_ctl.simple_command.return_value = {'StateName': 'Running'}
    with (
        patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl),
        patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach,
        patch('awx.main.tasks.system.reaper.reap_job') as mock_reap,
    ):
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    mock_reap.assert_not_called()
    mock_reattach.assert_called_once()


@pytest.mark.django_db
def test_adopt_job_async_no_timeout_on_terminal_state(me_inst, settings):
    """adopt_job_async does NOT timeout when work unit has terminal state."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id='unit-succeeded',
        started=now() - timedelta(seconds=7200),
    )

    mock_ctl = MagicMock()
    # Terminal state: status query succeeds with Succeeded
    mock_ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0}
    with patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl), patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach:
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    # Should reattach, NOT timeout
    mock_reattach.assert_called_once()


@pytest.mark.django_db
def test_adopt_job_async_no_timeout_on_already_adopted(me_inst, settings):
    """adopt_job_async does NOT timeout when work unit is already adopted."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(
        controller_node=me_inst.hostname,
        status='running',
        work_unit_id='unit-already-adopted',
        started=now() - timedelta(seconds=7200),
    )

    mock_ctl = MagicMock()
    # Already adopted response: no StateName field
    mock_ctl.simple_command.return_value = {'result': 'Already Adopted', 'unitid': 'unit-already-adopted'}
    with patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl), patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach:
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    # Should reattach, NOT timeout
    mock_reattach.assert_called_once()


@pytest.mark.django_db
def test_adopt_job_async_ctl_close_exception_is_swallowed(me_inst, settings):
    """adopt_job_async does not propagate exceptions from receptor_ctl.close()."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-close-err')

    mock_ctl = MagicMock()
    mock_ctl.close.side_effect = RuntimeError('socket already closed')

    with patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl), patch('awx.main.tasks.system.reattach_to_work_unit'):
        adopt_job_async(job.id, source_controller=me_inst.hostname)  # must not raise


@pytest.mark.django_db
def test_adopt_job_async_passes_unit_status_to_reattach(me_inst, settings):
    """adopt_job_async fetches unit_status once and passes it to reattach_to_work_unit."""
    from awx.main.tasks.system import adopt_job_async

    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', work_unit_id='unit-status-test')

    # Mock receptor_ctl to return a status dict
    mock_ctl = MagicMock()
    precached_status = {'StateName': 'Succeeded', 'ExitCode': 0, 'Detail': ''}
    mock_ctl.simple_command.return_value = precached_status

    with patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl), patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach:
        adopt_job_async(job.id, source_controller=me_inst.hostname)

    # Verify reattach_to_work_unit was called with unit_status parameter
    mock_reattach.assert_called_once()
    call_args, call_kwargs = mock_reattach.call_args
    assert 'unit_status' in call_kwargs
    assert call_kwargs['unit_status'] == precached_status


@pytest.mark.django_db
def test_adopt_job_async_recognizes_queue_time_transfer(me_inst, settings):
    """adopt_job_async proceeds when _reap_and_mark_lost_instance already transitioned the job."""
    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    lost_controller = 'lost-host'
    job = Job.objects.create(controller_node=lost_controller, status='running', work_unit_id='unit-queue-transfer')

    # Simulate the queue-time claim _reap_and_mark_lost_instance makes before publishing
    job.controller_node = django_settings.CLUSTER_HOST_ID
    job.save()

    mock_ctl = MagicMock()
    mock_ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0}

    with patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl), patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach:
        # Adoption still carries the lost controller as source, as published
        adopt_job_async(job.id, source_controller=lost_controller)

    # Verify adoption proceeded despite queue-time controller change
    mock_reattach.assert_called_once()


@pytest.mark.django_db
def test_adopt_job_async_atomic_claim_on_task_time(me_inst, settings):
    """adopt_job_async atomically claims job when still on source at task execution time."""
    settings.HADR_JOB_ADOPTION_TIMEOUT = 3600
    lost_controller = 'lost-host'
    job = Job.objects.create(controller_node=lost_controller, status='running', work_unit_id='unit-atomic-claim')
    # controller_node deliberately NOT changed: the task runs before any queue-time claim

    mock_ctl = MagicMock()
    mock_ctl.simple_command.return_value = {'StateName': 'Succeeded', 'ExitCode': 0}

    with patch('awx.main.tasks.system.get_receptor_ctl', return_value=mock_ctl), patch('awx.main.tasks.system.reattach_to_work_unit') as mock_reattach:
        # Adoption called with job still on lost_controller
        adopt_job_async(job.id, source_controller=lost_controller)

    # Verify job was atomically claimed
    job.refresh_from_db()
    assert job.controller_node == django_settings.CLUSTER_HOST_ID

    # Verify adoption proceeded after claim
    mock_reattach.assert_called_once()


# ── _finalize_job_run coverage ──────────────────────────────────────────────


@pytest.mark.django_db
def test_finalize_job_run_with_extra_fields(me_inst):
    """_finalize_job_run includes extra_fields in the update."""
    from awx.main.tasks.jobs import _finalize_job_run
    from awx.main.tasks.callback import RunnerCallback

    job = Job.objects.create(controller_node=me_inst.hostname, status='running')
    callback = RunnerCallback(model=Job)
    callback.instance = job
    callback.wrapup_event_dispatched = True

    _finalize_job_run(Job, job.pk, callback, 'successful', extra_fields={'elapsed': 100.5})

    job.refresh_from_db()
    assert job.status == 'successful'
    assert job.elapsed == 100.5


@pytest.mark.django_db
def test_finalize_job_run_update_model_returns_none(me_inst):
    """_finalize_job_run returns None when update_model fails."""
    from awx.main.tasks.jobs import _finalize_job_run
    from awx.main.tasks.callback import RunnerCallback

    callback = RunnerCallback(model=Job)
    callback.wrapup_event_dispatched = True

    with patch('awx.main.tasks.jobs.update_model', return_value=None):
        result = _finalize_job_run(Job, 99999, callback, 'successful')

    assert result is None


@pytest.mark.django_db
def test_finalize_job_run_with_blocked_jobs(me_inst):
    """_finalize_job_run schedules task manager when job has blocked dependents."""
    from awx.main.tasks.jobs import _finalize_job_run
    from awx.main.tasks.callback import RunnerCallback

    job = Job.objects.create(controller_node=me_inst.hostname, status='running')
    callback = RunnerCallback(model=Job)
    callback.instance = job
    callback.wrapup_event_dispatched = True

    with patch('awx.main.tasks.jobs.ScheduleTaskManager') as mock_tm:
        with patch('awx.main.tasks.jobs.update_model') as mock_update:
            # Create a mock instance that has unifiedjob_blocked_jobs
            mock_instance = MagicMock()
            mock_instance.unifiedjob_blocked_jobs.exists.return_value = True
            mock_update.return_value = mock_instance
            _finalize_job_run(Job, job.pk, callback, 'successful')
            mock_tm.return_value.schedule.assert_called()


@pytest.mark.django_db
def test_finalize_job_run_with_inventory_update(me_inst):
    """_finalize_job_run schedules inventory computed fields update for jobs with inventory."""
    from awx.main.tasks.jobs import _finalize_job_run
    from awx.main.tasks.callback import RunnerCallback
    from awx.main.models import Organization, Inventory

    org = Organization.objects.first()
    inv = Inventory.objects.create(name='test-inv', organization=org)
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', inventory=inv)

    callback = RunnerCallback(model=Job)
    callback.instance = job
    callback.wrapup_event_dispatched = True

    with patch('awx.main.tasks.jobs.update_inventory_computed_fields') as mock_delay:
        _finalize_job_run(Job, job.pk, callback, 'successful')
        mock_delay.delay.assert_called_once_with(inv.id)


@pytest.mark.django_db
def test_finalize_job_run_inventory_update_exception_logged(me_inst):
    """_finalize_job_run logs exception from inventory computed fields update."""
    from awx.main.tasks.jobs import _finalize_job_run
    from awx.main.tasks.callback import RunnerCallback
    from awx.main.models import Organization, Inventory

    org = Organization.objects.first()
    inv = Inventory.objects.create(name='test-inv-err', organization=org)
    job = Job.objects.create(controller_node=me_inst.hostname, status='running', inventory=inv)

    callback = RunnerCallback(model=Job)
    callback.instance = job
    callback.wrapup_event_dispatched = True

    with patch('awx.main.tasks.jobs.update_inventory_computed_fields') as mock_delay:
        mock_delay.delay.side_effect = RuntimeError('celery error')
        with patch('awx.main.tasks.jobs.logger') as mock_logger:
            _finalize_job_run(Job, job.pk, callback, 'successful')
            mock_logger.exception.assert_called()
