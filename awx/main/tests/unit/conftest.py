import pytest
import logging

from unittest.mock import PropertyMock

from awx.api.urls import urlpatterns as api_patterns
from awx.main.models import ExecutionEnvironment
from awx.main.models.credential import Credential, CredentialType

# Django
from django.urls import URLResolver, URLPattern


@pytest.fixture()
def execution_environment():
    return ExecutionEnvironment(name="test-ee", description="test-ee", managed=True)


@pytest.fixture(autouse=True)
def _disable_database_settings(mocker):
    m = mocker.patch('awx.conf.settings.SettingsWrapper.all_supported_settings', new_callable=PropertyMock)
    m.return_value = []


@pytest.fixture()
def all_views():
    """
    returns a set of all views in the app
    """
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
        'awx',  # logger name
        20,  # loglevel INFO
        './awx/some/module.py',  # pathname
        100,  # lineno
        'User joe logged in',  # msg
        tuple(),  # args,
        None,  # exc_info
    )


# Credential fixtures for workload identity tests
@pytest.fixture
def credentialtype_vault(db):
    vault_type = CredentialType.defaults['vault']()
    vault_type.save()
    return vault_type


@pytest.fixture
def credentialtype_ssh(db):
    ssh_type = CredentialType.defaults['ssh']()
    ssh_type.save()
    return ssh_type


@pytest.fixture
def credential(credentialtype_ssh):
    return Credential.objects.create(credential_type=credentialtype_ssh, name='test-cred', inputs={'username': 'u', 'password': 'p'})


@pytest.fixture
def vault_credential(credentialtype_vault):
    return Credential.objects.create(credential_type=credentialtype_vault, name='test-vault-cred', inputs={'vault_password': 'secret'})
