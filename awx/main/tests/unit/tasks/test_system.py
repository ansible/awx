import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from awx.main.tasks.system import (
    _check_in_this_instance,
    _receptor_mesh_status,
    _register_missing_this_instance,
    update_inventory_computed_fields,
)
from awx.main.models import Inventory
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


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_receptor_mesh_status_returns_status():
    ctl = MagicMock()
    ctl.simple_command.return_value = {'KnownConnectionCosts': {}}

    assert _receptor_mesh_status(ctl) == {'KnownConnectionCosts': {}}


def test_receptor_mesh_status_unavailable_is_none(mock_logger):
    ctl = MagicMock()
    ctl.simple_command.side_effect = OSError('socket gone')

    assert _receptor_mesh_status(ctl) is None


def _this_inst(lost=False, capacity=100, last_seen=NOW):
    inst = MagicMock(hostname='ctrl-0', capacity=capacity, last_seen=last_seen)
    inst.is_lost.return_value = lost
    return inst


def test_check_in_rejoining_instance_returns_false(mock_logger):
    inst = _this_inst(lost=True)

    assert _check_in_this_instance(inst, NOW) is False
    inst.local_health_check.assert_called_once_with()


def test_check_in_lost_instance_without_capacity_continues(mock_logger):
    assert _check_in_this_instance(_this_inst(lost=True, capacity=0), NOW) is True


@pytest.mark.parametrize('last_seen, warns', [(None, True), (NOW - timedelta(seconds=600), True), (NOW, False)])
def test_check_in_warns_on_missing_or_skewed_last_seen(mock_logger, last_seen, warns):
    assert _check_in_this_instance(_this_inst(last_seen=last_seen), NOW) is True
    assert mock_logger.warning.called is warns


@pytest.mark.parametrize('changed', [True, False])
def test_register_missing_this_instance_recreates_record(mock_logger, settings, changed):
    settings.AWX_AUTO_DEPROVISION_INSTANCES = True
    inst = MagicMock()
    with patch('awx.main.tasks.system.Instance.objects.register', return_value=(changed, inst)):
        assert _register_missing_this_instance() is inst
    inst.local_health_check.assert_called_once_with()
    assert mock_logger.warning.called is changed


def test_register_missing_this_instance_without_auto_deprovision(mock_logger, settings):
    settings.AWX_AUTO_DEPROVISION_INSTANCES = False

    assert _register_missing_this_instance() is None
    mock_logger.error.assert_called_once()
