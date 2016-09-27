import pytest


@pytest.fixture(autouse=True)
def _disable_database_settings(mocker):
    mocker.patch('awx.conf.settings.SettingsWrapper._get_supported_settings', return_value=[])
