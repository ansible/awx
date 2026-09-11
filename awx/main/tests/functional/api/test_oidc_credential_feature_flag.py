"""
Tests for OIDC workload identity credential type feature flag.

The FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED flag is an install-time flag that
controls whether OIDC credential types are loaded into the registry at startup.
When disabled, OIDC credential types are not loaded and do not exist in the database.
"""

import pytest
from unittest import mock

from django.test import override_settings

from awx.main.constants import OIDC_CREDENTIAL_TYPE_NAMESPACES
from awx.main.models.credential import CredentialType, ManagedCredentialType, load_credentials
from awx.api.versioning import reverse


@pytest.fixture
def reload_credentials_with_flag(django_db_setup, django_db_blocker):
    """
    Fixture that reloads credentials with a specific flag state.
    This simulates what happens at application startup.
    """
    # Save original registry state
    original_registry = ManagedCredentialType.registry.copy()

    def _reload(flag_enabled):
        with django_db_blocker.unblock():
            # Clear the entire registry before reloading
            ManagedCredentialType.registry.clear()

            # Reload credentials with the specified flag state
            with override_settings(FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED=flag_enabled):
                with mock.patch('awx.main.models.credential.detect_server_product_name', return_value='NOT_AWX'):
                    load_credentials()

            # Sync to database
            CredentialType.setup_tower_managed_defaults(lock=False)

            # In tests, the session fixture pre-loads all credential types into the DB.
            # Remove OIDC types when testing the disabled state so the API test is accurate.
            if not flag_enabled:
                CredentialType.objects.filter(namespace__in=OIDC_CREDENTIAL_TYPE_NAMESPACES).delete()

    yield _reload

    # Restore original registry state after tests
    ManagedCredentialType.registry.clear()
    ManagedCredentialType.registry.update(original_registry)


@pytest.fixture
def isolated_registry():
    """Save and restore the ManagedCredentialType registry, with full isolation via mocked entry_points."""
    original_registry = ManagedCredentialType.registry.copy()
    ManagedCredentialType.registry.clear()
    yield
    ManagedCredentialType.registry.clear()
    ManagedCredentialType.registry.update(original_registry)


def _make_mock_entry_point(name):
    """Create a mock entry point that mimics a credential plugin."""
    ep = mock.MagicMock()
    ep.name = name
    ep.value = f'test_plugin:{name}'
    plugin = mock.MagicMock(spec=[])
    ep.load.return_value = plugin
    return ep


def _mock_entry_points_factory(managed_names, supported_names):
    """Return a side_effect function for mocking entry_points() with controlled plugins."""
    managed = [_make_mock_entry_point(n) for n in managed_names]
    supported = [_make_mock_entry_point(n) for n in supported_names]

    def _entry_points(group):
        if group == 'awx_plugins.managed_credentials':
            return managed
        elif group == 'awx_plugins.managed_credentials.supported':
            return supported
        return []

    return _entry_points


# --- Unit tests for load_credentials() registry behavior ---


def test_oidc_types_in_registry_when_flag_enabled(isolated_registry):
    """Test that OIDC credential types are added to the registry when flag is enabled."""
    mock_eps = _mock_entry_points_factory(
        managed_names=['ssh', 'vault'],
        supported_names=['hashivault-kv-oidc', 'hashivault-ssh-oidc'],
    )
    with override_settings(FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED=True):
        with mock.patch('awx.main.models.credential.detect_server_product_name', return_value='NOT_AWX'):
            with mock.patch('awx.main.models.credential.entry_points', side_effect=mock_eps):
                load_credentials()

    for ns in OIDC_CREDENTIAL_TYPE_NAMESPACES:
        assert ns in ManagedCredentialType.registry, f"{ns} should be in registry when flag is enabled"
    assert 'ssh' in ManagedCredentialType.registry
    assert 'vault' in ManagedCredentialType.registry


def test_oidc_types_not_in_registry_when_flag_disabled(isolated_registry):
    """Test that OIDC credential types are excluded from the registry when flag is disabled."""
    mock_eps = _mock_entry_points_factory(
        managed_names=['ssh', 'vault'],
        supported_names=['hashivault-kv-oidc', 'hashivault-ssh-oidc'],
    )
    with override_settings(FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED=False):
        with mock.patch('awx.main.models.credential.detect_server_product_name', return_value='NOT_AWX'):
            with mock.patch('awx.main.models.credential.entry_points', side_effect=mock_eps):
                load_credentials()

    for ns in OIDC_CREDENTIAL_TYPE_NAMESPACES:
        assert ns not in ManagedCredentialType.registry, f"{ns} should not be in registry when flag is disabled"
    # Non-OIDC types should still be loaded
    assert 'ssh' in ManagedCredentialType.registry
    assert 'vault' in ManagedCredentialType.registry


def test_oidc_namespaces_constant():
    """Test that OIDC_CREDENTIAL_TYPE_NAMESPACES contains the expected namespaces."""
    assert 'hashivault-kv-oidc' in OIDC_CREDENTIAL_TYPE_NAMESPACES
    assert 'hashivault-ssh-oidc' in OIDC_CREDENTIAL_TYPE_NAMESPACES
    assert len(OIDC_CREDENTIAL_TYPE_NAMESPACES) == 2


# --- Functional API tests ---


@pytest.mark.django_db
def test_oidc_types_loaded_when_flag_enabled(get, admin, reload_credentials_with_flag):
    """Test that OIDC credential types are visible in the API when flag is enabled."""
    reload_credentials_with_flag(flag_enabled=True)

    response = get(reverse('api:credential_type_list'), admin)
    assert response.status_code == 200

    namespaces = [ct['namespace'] for ct in response.data['results']]
    assert 'hashivault-kv-oidc' in namespaces
    assert 'hashivault-ssh-oidc' in namespaces


@pytest.mark.django_db
def test_oidc_types_not_loaded_when_flag_disabled(get, admin, reload_credentials_with_flag):
    """Test that OIDC credential types are not visible in the API when flag is disabled."""
    reload_credentials_with_flag(flag_enabled=False)

    response = get(reverse('api:credential_type_list'), admin)
    assert response.status_code == 200

    namespaces = [ct['namespace'] for ct in response.data['results']]
    assert 'hashivault-kv-oidc' not in namespaces
    assert 'hashivault-ssh-oidc' not in namespaces

    # Verify they're also not in the database
    assert not CredentialType.objects.filter(namespace='hashivault-kv-oidc').exists()
    assert not CredentialType.objects.filter(namespace='hashivault-ssh-oidc').exists()
