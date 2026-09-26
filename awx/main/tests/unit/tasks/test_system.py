import pytest
from unittest.mock import MagicMock, patch
from awx.main.tasks.system import update_inventory_computed_fields
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


def test_purge_old_stdout_files_skips_when_dir_missing(mock_logger):
    # Regression test for ansible/awx#11903: the stdout directory is created
    # lazily on first job write, so a fresh/idle install can lack it. The task
    # should skip cleanly instead of raising FileNotFoundError.
    from awx.main.tasks.system import purge_old_stdout_files

    with patch("awx.main.tasks.system.settings.JOBOUTPUT_ROOT", "/nonexistent/awx/job_status"):
        with patch("awx.main.tasks.system.os.path.isdir", return_value=False):
            purge_old_stdout_files()

    mock_logger.debug.assert_called_once_with("Skipping stdout purge, /nonexistent/awx/job_status does not exist")


def test_purge_old_stdout_files_removes_expired_when_dir_present(mock_logger):
    from awx.main.tasks.system import purge_old_stdout_files

    with patch("awx.main.tasks.system.settings.JOBOUTPUT_ROOT", "/tmp/awx/job_status"):
        with patch("awx.main.tasks.system.os.path.isdir", return_value=True):
            with patch("awx.main.tasks.system.os.listdir", return_value=["old.out"]):
                with patch("awx.main.tasks.system.os.path.getctime", return_value=0.0):
                    with patch("awx.main.tasks.system.settings.LOCAL_STDOUT_EXPIRE_TIME", 3600):
                        with patch("awx.main.tasks.system.os.unlink") as mock_unlink:
                            purge_old_stdout_files()

    mock_unlink.assert_called_once_with("/tmp/awx/job_status/old.out")
