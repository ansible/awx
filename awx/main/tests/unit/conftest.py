import pytest
import logging

from mock import PropertyMock


@pytest.fixture(autouse=True)
def _disable_database_settings(mocker):
    m = mocker.patch('awx.conf.settings.SettingsWrapper.all_supported_settings', new_callable=PropertyMock)
    m.return_value = []


@pytest.fixture()
def dummy_log_record():
    return logging.LogRecord(
        'awx', # logger name
        20, # loglevel INFO
        './awx/some/module.py', # pathname
        100, # lineno
        'User joe logged in', # msg
        tuple(), # args,
        None # exc_info
    )
