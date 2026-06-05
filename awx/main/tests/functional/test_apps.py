import pytest

from django.apps import apps
from django.core.management.base import CommandError

from awx.main.tasks.system import _sync_credential_types_to_db


@pytest.fixture
def mock_setup_tower_managed_defaults(mocker):
    return mocker.patch('awx.main.models.credential.CredentialType.setup_tower_managed_defaults')


@pytest.mark.django_db
def test_sync_credential_types_migrations_ran(mocker, mock_setup_tower_managed_defaults):
    mocker.patch('awx.main.tasks.system.is_database_synchronized', return_value=True)

    _sync_credential_types_to_db()

    mock_setup_tower_managed_defaults.assert_called_once()


@pytest.mark.django_db
def test_sync_credential_types_migrations_not_ran(mocker, mock_setup_tower_managed_defaults):
    mocker.patch('awx.main.tasks.system.is_database_synchronized', return_value=False)

    _sync_credential_types_to_db()

    mock_setup_tower_managed_defaults.assert_not_called()


def test_check_db_requirement_no_violations(mocker):
    mocker.patch('awx.main.apps.db_requirement_violations', return_value=None)
    main_config = apps.get_app_config('main')

    result = main_config.check_db_requirement()

    assert result is None


def test_check_db_requirement_with_violations(mocker):
    violation_msg = "Database version check failed"
    mocker.patch('awx.main.apps.db_requirement_violations', return_value=violation_msg)
    main_config = apps.get_app_config('main')

    with pytest.raises(CommandError) as exc_info:
        main_config.check_db_requirement()

    assert str(exc_info.value) == violation_msg
