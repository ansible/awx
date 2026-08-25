import pytest
from unittest.mock import MagicMock, patch, call
from awx.main.tasks.system import _heartbeat_instance_management, update_inventory_computed_fields, inspect_execution_and_hop_nodes
from awx.main.models import Instance, Inventory
from django.db import DatabaseError


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
