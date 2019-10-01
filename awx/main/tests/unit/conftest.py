import pytest
import logging

from unittest.mock import PropertyMock

from awx.api.urls import urlpatterns as api_patterns

# Django
from django.urls import URLResolver, URLPattern


@pytest.fixture(autouse=True)
def _disable_database_settings(mocker):
    m = mocker.patch('awx.conf.settings.SettingsWrapper.all_supported_settings', new_callable=PropertyMock)
    m.return_value = []


@pytest.fixture()
def all_views():
    '''
    returns a set of all views in the app
    '''
    patterns = set()
    url_views = set()
    # Add recursive URL patterns
    unprocessed = set(api_patterns)
    while unprocessed:
        to_process = unprocessed.copy()
        unprocessed = set()
        for pattern in to_process:
            if hasattr(pattern, 'lookup_str') and not pattern.lookup_str.startswith('awx.api'):
                continue
            patterns.add(pattern)
            if isinstance(pattern, URLResolver):
                for sub_pattern in pattern.url_patterns:
                    if sub_pattern not in patterns:
                        unprocessed.add(sub_pattern)
    # Get view classes
    for pattern in patterns:
        if isinstance(pattern, URLPattern) and hasattr(pattern.callback, 'view_class'):
            url_views.add(pattern.callback.view_class)
    return url_views


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
