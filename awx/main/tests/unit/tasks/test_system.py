import pytest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch
from awx.main.tasks.system import (
    _heartbeat_instance_management,
    update_inventory_computed_fields,
    inspect_execution_and_hop_nodes,
    _mesh_all_ready_nodes_visible,
    _heartbeat_handle_lost_instances,
    _reap_and_mark_lost_instance,
)
from awx.main.models import Instance, Inventory
from django.db import DatabaseError
from django.utils.timezone import now, timedelta


# ── Helpers ───────────────────────────────────────────────────────────────────


def _instance(hostname, node_type='execution', node_state='ready', last_seen_secs_ago=0):
    """Build a mock instance. last_seen_secs_ago: how old the last_seen timestamp is."""
    inst = MagicMock()
    inst.hostname = hostname
    inst.node_type = node_type
    inst.node_state = node_state
    inst.last_seen = now() - timedelta(seconds=last_seen_secs_ago)
    return inst


_UNSET = object()  # sentinel so callers can explicitly pass None (JSON null from receptor)


def _mesh_status(known_costs=_UNSET, advertisements=_UNSET):
    return {
        'KnownConnectionCosts': {} if known_costs is _UNSET else known_costs,
        'Advertisements': [] if advertisements is _UNSET else [{'NodeID': n} for n in (advertisements or [])],
    }


def _mock_ctl(status):
    ctl = MagicMock()
    ctl.simple_command.return_value = status
    return ctl


# ── Tests: _mesh_all_ready_nodes_visible ──────────────────────────────────────


class TestMeshAllReadyNodesVisible:
    """Gate uses KnownConnectionCosts (receptor routing table) as the stability signal.

    No DB state is consulted — KnownConnectionCosts is maintained entirely by
    receptor's routing protocol. Empty table = routing not yet established (Window A).
    """

    def test_defers_when_routing_table_empty(self):
        """Gate defers when KnownConnectionCosts is empty.

        Window A scenario: fresh receptor after controller restart — routing gossip
        has not yet propagated. Empty dict means no connections are established.
        """
        status = _mesh_status(known_costs={}, advertisements=['ee-0', 'ee-1'])
        assert _mesh_all_ready_nodes_visible(status) is False

    def test_defers_when_routing_table_null(self):
        """Gate defers when KnownConnectionCosts is JSON null (Go nil map → Python None).

        Receptor is a Go service; a nil map marshals to JSON null, which Python's json
        decoder represents as None. Treated the same as an empty routing table.
        """
        status = _mesh_status(known_costs=None, advertisements=['ee-0'])
        assert _mesh_all_ready_nodes_visible(status) is False

    def test_passes_when_routing_established(self):
        """Gate passes when KnownConnectionCosts is populated.

        Any non-empty routing table means receptor's gossip has propagated and
        the mesh is stable enough to trust peer-judgment decisions.
        """
        status = _mesh_status(known_costs={'ctrl-0': {'ee-0': 1}}, advertisements=['ee-0'])
        assert _mesh_all_ready_nodes_visible(status) is True

    def test_passes_when_routing_established_dead_ee_not_in_routing(self):
        """Gate passes even when a dead EE is absent from routing.

        A genuinely dead EE won't appear in KnownConnectionCosts (no active
        connections to gossip it). The gate correctly ignores its absence because
        it only checks whether routing is established at all, not which nodes appear.
        The dead EE will be caught by normal lost-instance handling.
        """
        status = _mesh_status(
            known_costs={'ctrl-0': {'live-ee': 1}},  # dead-ee absent — but routing is up
            advertisements=['live-ee'],
        )
        assert _mesh_all_ready_nodes_visible(status) is True

    def test_fails_open_when_mesh_status_none(self):
        """Gate fails open when mesh_status is None (receptor status fetch failed).

        If the caller couldn't fetch status, we can't assess mesh stability.
        Fail open so existing peer-judgment error paths are not bypassed.
        """
        assert _mesh_all_ready_nodes_visible(None) is True


# ── Tests: _heartbeat_handle_lost_instances (task manager lock) ───────────────


def _make_lock(acquired):
    """Return a context manager factory that always yields the given acquired bool."""

    @contextmanager
    def _lock(name, wait=True, **kwargs):
        yield acquired

    return _lock


def _make_lock_sequence(sequence):
    """Return a context manager factory that yields values from sequence in order."""
    it = iter(sequence)

    @contextmanager
    def _lock(name, wait=True, **kwargs):
        yield next(it)

    return _lock


def _lost_instance(hostname='ctrl-1'):
    inst = MagicMock()
    inst.hostname = hostname
    inst.node_type = 'control'
    inst.node_state = 'ready'
    return inst


class TestHeartbeatHandleLostInstancesLock:
    def _run(self, lost, this_inst=None):
        if this_inst is None:
            this_inst = MagicMock()
        with (
            patch('awx.main.tasks.system.reaper') as mock_reaper,
            patch('awx.main.tasks.system.UnifiedJob') as mock_uj,
            patch('awx.main.tasks.system.settings') as mock_settings,
        ):
            mock_settings.AWX_AUTO_DEPROVISION_INSTANCES = False
            _heartbeat_handle_lost_instances(lost, this_inst)
            return mock_reaper, mock_uj

    def test_processes_instance_when_lock_acquired(self):
        """When the lock is acquired, reap and mark_offline are both called."""
        inst = _lost_instance()
        with patch('awx.main.tasks.system.advisory_lock', _make_lock(True)):
            mock_reaper, _ = self._run([inst])
        mock_reaper.reap.assert_called_once_with(inst, job_explanation='Job reaped due to instance shutdown')
        inst.mark_offline.assert_called_once()

    def test_skips_instance_when_lock_unavailable(self):
        """When the lock is unavailable, reap and mark_offline are not called."""
        inst = _lost_instance()
        with patch('awx.main.tasks.system.advisory_lock', _make_lock(False)):
            mock_reaper, _ = self._run([inst])
        mock_reaper.reap.assert_not_called()
        inst.mark_offline.assert_not_called()

    def test_logs_when_instance_deferred(self):
        """When the lock is unavailable, a log message is emitted with the hostname."""
        inst = _lost_instance('ctrl-1')
        with patch('awx.main.tasks.system.advisory_lock', _make_lock(False)), patch('awx.main.tasks.system.logger') as mock_log:
            self._run([inst])
        assert mock_log.info.called
        logged = mock_log.info.call_args[0][0]
        assert 'ctrl-1' in logged

    def test_per_instance_lock_first_skipped_second_processed(self):
        """Lock alternates False/True: first instance skipped, second processed."""
        inst1 = _lost_instance('ctrl-1')
        inst2 = _lost_instance('ctrl-2')
        with patch('awx.main.tasks.system.advisory_lock', _make_lock_sequence([False, True])):
            mock_reaper, _ = self._run([inst1, inst2])
        mock_reaper.reap.assert_called_once_with(inst2, job_explanation='Job reaped due to instance shutdown')
        inst1.mark_offline.assert_not_called()
        inst2.mark_offline.assert_called_once()

    def test_all_instances_processed_when_lock_always_acquired(self):
        """When lock is always acquired, all instances are fully processed."""
        inst1 = _lost_instance('ctrl-1')
        inst2 = _lost_instance('ctrl-2')
        with patch('awx.main.tasks.system.advisory_lock', _make_lock(True)):
            mock_reaper, _ = self._run([inst1, inst2])
        assert mock_reaper.reap.call_count == 2
        inst1.mark_offline.assert_called_once()
        inst2.mark_offline.assert_called_once()


# ── Tests: _reap_and_mark_lost_instance (exception / branch coverage) ────────


class TestReapAndMarkLostInstance:
    def _run(self, inst, auto_deprovision=False, reap_side_effect=None, mark_offline_side_effect=None):
        with (
            patch('awx.main.tasks.system.reaper') as mock_reaper,
            patch('awx.main.tasks.system.UnifiedJob'),
            patch('awx.main.tasks.system.settings') as mock_s,
        ):
            mock_s.AWX_AUTO_DEPROVISION_INSTANCES = auto_deprovision
            if reap_side_effect is not None:
                mock_reaper.reap.side_effect = reap_side_effect
            if mark_offline_side_effect is not None:
                inst.mark_offline.side_effect = mark_offline_side_effect
            _reap_and_mark_lost_instance(inst)
        return mock_reaper

    def test_reap_exception_does_not_prevent_mark_offline(self):
        """Exception during reap is logged but mark_offline still runs.

        The first try block isolates reap/update failures from the mark-offline logic.
        """
        inst = _lost_instance()
        self._run(inst, reap_side_effect=Exception('receptor timeout'))
        inst.mark_offline.assert_called_once()

    def test_auto_deprovision_deletes_control_node(self):
        """AWX_AUTO_DEPROVISION_INSTANCES=True: control node is deleted, not marked offline."""
        inst = _lost_instance()
        inst.node_type = 'control'
        self._run(inst, auto_deprovision=True)
        inst.delete.assert_called_once()
        inst.mark_offline.assert_not_called()

    def test_skips_mark_offline_when_node_already_unavailable(self):
        """Node in a non-READY state is not marked offline again (it's already handled)."""
        inst = _lost_instance()
        inst.node_state = 'unavailable'
        self._run(inst)
        inst.mark_offline.assert_not_called()

    def test_database_error_without_sqlstate_logs_exception(self):
        """DatabaseError with no __cause__ sqlstate logs the generic error message."""
        inst = _lost_instance()
        err = DatabaseError('constraint violation')
        err.__cause__ = None
        with patch('awx.main.tasks.system.logger') as mock_log:
            self._run(inst, mark_offline_side_effect=err)
        assert mock_log.exception.called
        assert 'No SQL state' in mock_log.exception.call_args[0][0]

    def test_database_error_with_sqlstate_logs_details(self):
        """DatabaseError with a cause.sqlstate invokes psycopg.errors.lookup for the state string."""
        inst = _lost_instance()
        err = DatabaseError('unique violation')

        class _FakePsycopgError(Exception):
            sqlstate = 'some_state'

        err.__cause__ = _FakePsycopgError('underlying pg error')
        with (
            patch('awx.main.tasks.system.logger') as mock_log,
            patch('awx.main.tasks.system.psycopg') as mock_psycopg,
        ):
            mock_psycopg.errors.lookup.return_value = 'SomeError'
            mock_psycopg.errors.NoData = 'other_state'  # ensure non-NoData branch
            self._run(inst, mark_offline_side_effect=err)
        mock_psycopg.errors.lookup.assert_called_once_with('some_state')
        assert mock_log.exception.called

    def test_database_error_with_nodata_sqlstate_logs_debug(self):
        """NoData sqlstate means another controller already marked the instance lost — log at debug."""
        inst = _lost_instance()
        err = DatabaseError('nodata')

        class _FakePsycopgError(Exception):
            sqlstate = 'nodata_state'

        err.__cause__ = _FakePsycopgError('nodata cause')
        with (
            patch('awx.main.tasks.system.logger') as mock_log,
            patch('awx.main.tasks.system.psycopg') as mock_psycopg,
        ):
            mock_psycopg.errors.lookup.return_value = 'NoData'
            mock_psycopg.errors.NoData = 'nodata_state'  # match the sqlstate
            self._run(inst, mark_offline_side_effect=err)
        mock_log.exception.assert_not_called()
        debug_messages = [str(call) for call in mock_log.debug.call_args_list]
        assert any('marked' in m for m in debug_messages)


@pytest.fixture
def mock_logger():
    with patch("awx.main.tasks.system.logger") as logger:
        yield logger


@pytest.fixture
def mock_inventory():
    return MagicMock(spec=Inventory)


def test_update_inventory_computed_fields_existing_inventory(mock_logger, mock_inventory):
    # Mocking the Inventory.objects.filter method to return a non-empty queryset
    with patch("awx.main.tasks.system.Inventory.objects.filter") as mock_filter:
        mock_filter.return_value.exists.return_value = True
        mock_filter.return_value.__getitem__.return_value = mock_inventory

        # Mocking the update_computed_fields method
        with patch.object(mock_inventory, "update_computed_fields") as mock_update_computed_fields:
            update_inventory_computed_fields(1)

            # Assertions
            mock_filter.assert_called_once_with(id=1)
            mock_update_computed_fields.assert_called_once()

            # You can add more assertions based on your specific requirements


def test_update_inventory_computed_fields_missing_inventory(mock_logger):
    # Mocking the Inventory.objects.filter method to return an empty queryset
    with patch("awx.main.tasks.system.Inventory.objects.filter") as mock_filter:
        mock_filter.return_value.exists.return_value = False

        update_inventory_computed_fields(1)

        # Assertions
        mock_filter.assert_called_once_with(id=1)
        mock_logger.error.assert_called_once_with("Update Inventory Computed Fields failed due to missing inventory: 1")


def test_update_inventory_computed_fields_database_error_nosqlstate(mock_logger, mock_inventory):
    # Mocking the Inventory.objects.filter method to return a non-empty queryset
    with patch("awx.main.tasks.system.Inventory.objects.filter") as mock_filter:
        mock_filter.return_value.exists.return_value = True
        mock_filter.return_value.__getitem__.return_value = mock_inventory

        # Mocking the update_computed_fields method
        with patch.object(mock_inventory, "update_computed_fields") as mock_update_computed_fields:
            # Simulating the update_computed_fields method to explicitly raise a DatabaseError
            mock_update_computed_fields.side_effect = DatabaseError("Some error")

            update_inventory_computed_fields(1)

            # Assertions
            mock_filter.assert_called_once_with(id=1)
            mock_update_computed_fields.assert_called_once()
            mock_inventory.update_computed_fields.assert_called_once()


@patch('awx.main.tasks.system.inspect_execution_and_hop_nodes')
@patch('awx.main.tasks.system._mesh_all_ready_nodes_visible', return_value=False)
@patch('awx.main.tasks.system.get_receptor_ctl')
@patch('awx.main.tasks.system.Instance.objects.filter')
def test_heartbeat_defers_lost_instances_when_mesh_gate_blocks(mock_filter, mock_get_ctl, mock_gate, mock_inspect):
    """When the mesh gate returns False, lost_instances is returned empty (peer judgment deferred)."""
    this_inst = MagicMock(spec=Instance)
    this_inst.hostname = 'ctrl-0'
    this_inst.is_lost.return_value = False
    this_inst.last_seen = now() - timedelta(seconds=30)

    lost_peer = MagicMock(spec=Instance)
    lost_peer.hostname = 'ctrl-1'
    lost_peer.is_lost.return_value = True

    mock_filter.return_value = [this_inst, lost_peer]

    with patch('awx.main.tasks.system.settings') as mock_settings:
        mock_settings.CLUSTER_HOST_ID = 'ctrl-0'
        mock_settings.CLUSTER_NODE_HEARTBEAT_PERIOD = 60
        _, _, lost_result = _heartbeat_instance_management()

    assert lost_result == []
    # Gate is called with mesh_status (not instance_list) — just verify it was called
    mock_gate.assert_called_once()


@patch('awx.main.tasks.system.get_receptor_ctl', side_effect=FileNotFoundError)
@patch('awx.main.tasks.system.Instance.objects.filter')
def test_heartbeat_marks_offline_when_receptor_unavailable(mock_filter, mock_get_ctl):
    this_inst = MagicMock(spec=Instance)
    this_inst.hostname = 'test-host'
    mock_filter.return_value = [this_inst]

    with patch('awx.main.tasks.system.settings') as mock_settings:
        mock_settings.CLUSTER_HOST_ID = 'test-host'
        result = _heartbeat_instance_management()

    assert result == (None, None, None)
    this_inst.local_health_check.assert_called_once()
    this_inst.mark_offline.assert_called_once_with(errors='Receptor not available')


class TestInspectExecutionAndHopNodes:
    """Tests for inspect_execution_and_hop_nodes, which now accepts pre-fetched mesh_status."""

    @patch('awx.main.tasks.system.inspect_established_receptor_connections')
    @patch('awx.main.tasks.system.advisory_lock')
    def test_skips_when_lock_not_acquired(self, mock_lock, mock_inspect_conns):
        mock_lock.return_value.__enter__ = MagicMock(return_value=False)
        mock_lock.return_value.__exit__ = MagicMock(return_value=False)

        inspect_execution_and_hop_nodes([], _mesh_status())

        mock_inspect_conns.assert_not_called()

    @patch('awx.main.tasks.system.inspect_established_receptor_connections')
    @patch('awx.main.tasks.system.advisory_lock')
    def test_skips_when_mesh_status_none(self, mock_lock, mock_inspect_conns):
        """When mesh_status is None (status fetch failed), skip all inspection."""
        mock_lock.return_value.__enter__ = MagicMock(return_value=True)
        mock_lock.return_value.__exit__ = MagicMock(return_value=False)

        inspect_execution_and_hop_nodes([], None)

        mock_inspect_conns.assert_not_called()

    @patch('awx.main.tasks.system.inspect_established_receptor_connections')
    @patch('awx.main.tasks.system.advisory_lock')
    def test_runs_when_lock_acquired(self, mock_lock, mock_inspect_conns):
        mock_lock.return_value.__enter__ = MagicMock(return_value=True)
        mock_lock.return_value.__exit__ = MagicMock(return_value=False)

        inspect_execution_and_hop_nodes([], _mesh_status())

        mock_inspect_conns.assert_called_once()

    @patch('awx.main.tasks.system.inspect_established_receptor_connections')
    @patch('awx.main.tasks.system.advisory_lock')
    def test_updates_last_seen_for_execution_nodes(self, mock_lock, mock_inspect_conns):
        mock_lock.return_value.__enter__ = MagicMock(return_value=True)
        mock_lock.return_value.__exit__ = MagicMock(return_value=False)

        exec_node = MagicMock(spec=Instance)
        exec_node.hostname = 'exec-1'
        exec_node.node_type = 'execution'
        exec_node.node_state = 'ready'
        exec_node.last_seen = None
        exec_node.capacity = 100
        exec_node.enabled = True
        exec_node.cpu = 4
        exec_node.memory = 8000000000

        control_node = MagicMock(spec=Instance)
        control_node.hostname = 'control-1'
        control_node.node_type = 'control'

        status = _mesh_status(
            known_costs={},
            advertisements=['exec-1', 'control-1'],
        )
        # Override Advertisements to include Time field required by the function
        status['Advertisements'] = [
            {'NodeID': 'exec-1', 'Time': '2026-01-01T00:00:00+00:00'},
            {'NodeID': 'control-1', 'Time': '2026-01-01T00:00:00+00:00'},
        ]

        inspect_execution_and_hop_nodes([exec_node, control_node], status)

        exec_node.save.assert_called_once_with(update_fields=['last_seen'])
        control_node.save.assert_not_called()
