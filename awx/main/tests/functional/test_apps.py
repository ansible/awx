import pytest

from django.apps import apps
from django.core.management.base import CommandError

from awx.main.apps import MainConfig
from awx.main.tasks.system import _sync_credential_types_to_db, _sync_managed_role_definitions_to_db


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


def test_sync_managed_role_definitions_gateway_locked(mocker):
    """Gateway 423 during awx-manage migrate must not abort the migration (AAP-82221 regression).

    The sync is deferred and retried by _sync_managed_role_definitions_to_db()
    at dispatcher startup once the gateway is ready.
    """
    mocker.patch(
        'awx.main.migrations._dab_rbac.setup_managed_role_definitions',
        side_effect=Exception('423 Client Error: Locked — migrate_service_data not complete'),
    )
    mock_warning = mocker.patch('awx.main.apps.logger.warning')

    # Must not raise even when the gateway rejects the sync
    MainConfig._sync_managed_role_definitions(sender=None)

    mock_warning.assert_called_once()


@pytest.mark.django_db
def test_sync_managed_role_definitions_to_db_runs_when_synced(mocker):
    """At dispatcher startup, managed role definitions are synced when migrations are current."""
    mocker.patch('awx.main.tasks.system.is_database_synchronized', return_value=True)
    mock_setup = mocker.patch('awx.main.migrations._dab_rbac.setup_managed_role_definitions')

    _sync_managed_role_definitions_to_db()

    mock_setup.assert_called_once()


@pytest.mark.django_db
def test_sync_managed_role_definitions_to_db_skips_when_not_synced(mocker):
    """Sync is skipped if migrations have not been applied yet."""
    mocker.patch('awx.main.tasks.system.is_database_synchronized', return_value=False)
    mock_setup = mocker.patch('awx.main.migrations._dab_rbac.setup_managed_role_definitions')

    _sync_managed_role_definitions_to_db()

    mock_setup.assert_not_called()


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
