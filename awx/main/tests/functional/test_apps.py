import pytest

from django.apps import apps


@pytest.fixture
def mock_setup_tower_managed_defaults(mocker):
    return mocker.patch('awx.main.models.credential.CredentialType.setup_tower_managed_defaults')


@pytest.mark.django_db
def test_load_credential_types_feature_migrations_ran(mocker, mock_setup_tower_managed_defaults):
    mocker.patch('awx.main.apps.is_database_synchronized', return_value=True)

    apps.get_app_config('main')._load_credential_types_feature()

    mock_setup_tower_managed_defaults.assert_called_once()


@pytest.mark.django_db
def test_load_credential_types_feature_migrations_not_ran(mocker, mock_setup_tower_managed_defaults):
    mocker.patch('awx.main.apps.is_database_synchronized', return_value=False)

    apps.get_app_config('main')._load_credential_types_feature()

    mock_setup_tower_managed_defaults.assert_not_called()
