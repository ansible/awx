import pytest
from mock import PropertyMock


@pytest.fixture(autouse=True)
def _disable_database_settings(mocker):
    m = mocker.patch('awx.conf.settings.SettingsWrapper.all_supported_settings', new_callable=PropertyMock)
    m.return_value = []

