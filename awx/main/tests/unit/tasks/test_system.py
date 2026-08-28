import pytest
from unittest.mock import MagicMock, patch
from awx.main.tasks.system import _heartbeat_instance_management, update_inventory_computed_fields, inspect_execution_and_hop_nodes, _mesh_all_ready_nodes_visible
from awx.main.models import Instance, Inventory
from django.db import DatabaseError


# ── Helpers ───────────────────────────────────────────────────────────────────


def _instance(hostname, node_type='execution', node_state='ready'):
    inst = MagicMock()
    inst.hostname = hostname
    inst.node_type = node_type
    inst.node_state = node_state
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
    def test_passes_when_all_nodes_visible(self):
        """Gate passes when all READY EE/hop nodes appear in both tables."""
        nodes = [
            _instance('ee-0', 'execution', 'ready'),
            _instance('ee-1', 'execution', 'ready'),
            _instance('hop-0', 'hop', 'ready'),
            _instance('ctrl-0', 'control', 'ready'),  # controls never checked
        ]
        status = _mesh_status(
            known_costs={'ee-0': {}, 'ee-1': {}, 'hop-0': {}},
            advertisements=['ee-0', 'ee-1', 'hop-0'],
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_blocks_window_a_ee_absent_from_routing(self):
        """Gate blocks (Window A) when EEs absent from KnownConnectionCosts.

        Scenario: fresh receptor after controller restart — routing table not yet propagated.
        """
        nodes = [_instance('ee-0'), _instance('ee-1')]
        status = _mesh_status(
            known_costs={'ctrl-0': {}},  # EEs not in routing table yet
            advertisements=['ee-0', 'ee-1'],
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            assert _mesh_all_ready_nodes_visible(nodes) is False

    def test_blocks_window_b_ee_absent_from_advertisements(self):
        """Gate blocks (Window B) when EEs are routable but not yet advertising.

        Scenario: t=3-60s after restart — routing propagated but EEs haven't
        re-advertised yet (advertisement period = 60s, fresh receptor has no cache).
        """
        nodes = [_instance('ee-0'), _instance('ee-1')]
        status = _mesh_status(
            known_costs={'ee-0': {}, 'ee-1': {}},  # routing restored
            advertisements=['ctrl-0'],  # but no EE advertisements yet
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            assert _mesh_all_ready_nodes_visible(nodes) is False

    def test_fails_open_when_receptor_socket_missing(self):
        """Gate fails open on FileNotFoundError (receptor not yet started)."""
        nodes = [_instance('ee-0')]
        with patch('awx.main.tasks.system.get_receptor_ctl', side_effect=FileNotFoundError):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_fails_open_when_receptor_status_fails(self):
        """Gate fails open when receptorctl status raises ValueError."""
        nodes = [_instance('ee-0')]
        ctl = MagicMock()
        ctl.simple_command.side_effect = ValueError('connection reset')
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=ctl):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_fails_open_on_oserror(self):
        """Gate fails open on OSError (stale socket — exists but daemon not accepting).

        A present-but-unresponsive socket raises OSError/ConnectionRefusedError, not
        FileNotFoundError. This is the exact scenario during a controller restart window.
        """
        nodes = [_instance('ee-0')]
        with patch('awx.main.tasks.system.get_receptor_ctl', side_effect=OSError('Connection refused')):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_fails_open_on_runtime_error(self):
        """Gate fails open on RuntimeError (receptor handshake or protocol error)."""
        nodes = [_instance('ee-0')]
        ctl = MagicMock()
        ctl.simple_command.side_effect = RuntimeError('Failed to connect to Receptor socket')
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=ctl):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_fails_open_when_receptor_returns_null_known_costs(self):
        """Gate fails open when KnownConnectionCosts is JSON null (Go nil map → Python None).

        Receptor is a Go service; a nil map marshals to JSON null, which Python's json
        decoder represents as None. This is most likely during Window A (fresh startup
        with no established connections yet). set(None) would raise TypeError without
        the `or {}` guard.
        """
        nodes = [_instance('ee-0')]
        status = _mesh_status(known_costs=None, advertisements=['ee-0'])
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            # None KnownConnectionCosts → ee-0 absent from routing → gate blocks (Window A)
            assert _mesh_all_ready_nodes_visible(nodes) is False

    def test_fails_open_when_receptor_returns_null_advertisements(self):
        """Gate blocks when Advertisements is JSON null (Go nil slice → Python None).

        This is Window B: routing is established but no service advertisements yet.
        `for ad in None` would raise TypeError without the `or []` guard.
        """
        nodes = [_instance('ee-0')]
        status = _mesh_status(known_costs={'ee-0': {}}, advertisements=None)
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            # None Advertisements → ee-0 absent from ads → gate blocks (Window B)
            assert _mesh_all_ready_nodes_visible(nodes) is False

    def test_passes_trivially_with_no_ee_or_hop_nodes(self):
        """Gate passes immediately when instance_list has only control nodes.

        No receptor call is made — nothing to check.
        """
        nodes = [_instance('ctrl-0', 'control', 'ready')]
        with patch('awx.main.tasks.system.get_receptor_ctl') as mock_ctl:
            assert _mesh_all_ready_nodes_visible(nodes) is True
        mock_ctl.assert_not_called()

    def test_receptor_not_called_when_expected_set_is_empty(self):
        """Gate returns True without calling receptor when no READY EE/hop nodes exist.

        If `expected` is empty (e.g. control-only cluster, or all EEs are UNAVAILABLE),
        the gate short-circuits before making a receptor call. This also validates that
        control nodes are never included in the expected set.
        """
        nodes = [
            _instance('ctrl-0', 'control', 'ready'),
            _instance('ee-down', 'execution', 'unavailable'),
        ]
        with patch('awx.main.tasks.system.get_receptor_ctl') as mock_ctl:
            assert _mesh_all_ready_nodes_visible(nodes) is True
        mock_ctl.assert_not_called()

    def test_ignores_unavailable_ee_nodes(self):
        """Gate only checks READY nodes — already-UNAVAILABLE EEs are excluded.

        An EE that is already UNAVAILABLE should not be in expected; the gate
        should not fail if that EE is missing from the mesh tables.
        """
        nodes = [
            _instance('ee-down', 'execution', 'unavailable'),
            _instance('ee-up', 'execution', 'ready'),
        ]
        status = _mesh_status(
            known_costs={'ee-up': {}},  # only the READY EE present
            advertisements=['ee-up'],
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            assert _mesh_all_ready_nodes_visible(nodes) is True

    def test_instance_list_plus_lost_covers_removed_ees(self):
        """Caller must pass instance_list + lost_instances, not just instance_list.

        The peer-judgment loop removes lost EEs from instance_list before the gate
        runs. If only instance_list is passed, expected is empty and the gate always
        returns True. This test proves the gate correctly catches Window B when given
        the combined list.
        """
        ee0 = _instance('ee-0')
        ee1 = _instance('ee-1')

        # Simulate the state after peer-judgment loop:
        # instance_list had EEs removed; lost_instances holds them.
        instance_list_after_loop = []  # EEs already removed
        lost_instances = [ee0, ee1]  # peer-judgment put them here

        status = _mesh_status(
            known_costs={'ee-0': {}, 'ee-1': {}},
            advertisements=['ctrl-0'],  # no EE ads → Window B
        )
        with patch('awx.main.tasks.system.get_receptor_ctl', return_value=_mock_ctl(status)):
            # Wrong: passing only instance_list (empty) → gate returns True (bug)
            assert _mesh_all_ready_nodes_visible(instance_list_after_loop) is True

            # Correct: passing combined list → gate catches Window B (returns False)
            assert _mesh_all_ready_nodes_visible(instance_list_after_loop + lost_instances) is False


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
    """Tests for the advisory_lock guard in inspect_execution_and_hop_nodes."""

    @patch('awx.main.tasks.system.inspect_established_receptor_connections')
    @patch('awx.main.tasks.system.advisory_lock')
    def test_skips_when_lock_not_acquired(self, mock_lock, mock_inspect_conns):
        mock_lock.return_value.__enter__ = MagicMock(return_value=False)
        mock_lock.return_value.__exit__ = MagicMock(return_value=False)
        receptor_ctl = MagicMock()

        inspect_execution_and_hop_nodes([], receptor_ctl)

        receptor_ctl.simple_command.assert_not_called()
        mock_inspect_conns.assert_not_called()

    @patch('awx.main.tasks.system.inspect_established_receptor_connections')
    @patch('awx.main.tasks.system.advisory_lock')
    def test_runs_when_lock_acquired(self, mock_lock, mock_inspect_conns):
        mock_lock.return_value.__enter__ = MagicMock(return_value=True)
        mock_lock.return_value.__exit__ = MagicMock(return_value=False)
        receptor_ctl = MagicMock()
        receptor_ctl.simple_command.return_value = {'Advertisements': [], 'KnownConnectionCosts': {}}

        inspect_execution_and_hop_nodes([], receptor_ctl)

        receptor_ctl.simple_command.assert_called_once_with('status')
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

        receptor_ctl = MagicMock()
        receptor_ctl.simple_command.return_value = {
            'Advertisements': [
                {'NodeID': 'exec-1', 'Time': '2026-01-01T00:00:00+00:00'},
                {'NodeID': 'control-1', 'Time': '2026-01-01T00:00:00+00:00'},
            ],
            'KnownConnectionCosts': {},
        }

        inspect_execution_and_hop_nodes([exec_node, control_node], receptor_ctl)

        exec_node.save.assert_called_once_with(update_fields=['last_seen'])
        control_node.save.assert_not_called()
