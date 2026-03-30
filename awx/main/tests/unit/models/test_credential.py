# -*- coding: utf-8 -*-

import pytest

from types import SimpleNamespace
from unittest import mock

from awx.main.models import Credential, CredentialType
from awx.main.models.credential import CredentialTypeHelper, ManagedCredentialType

from django.apps import apps


@pytest.mark.django_db
def test_unique_hash_with_unicode():
    ct = CredentialType.objects.create(name='Väult', kind='vault')
    cred = Credential.objects.create(name='Iñtërnâtiônàlizætiøn', credential_type=ct, inputs={'vault_id': '🐉🐉🐉'})
    assert cred.unique_hash(display=True) == 'Väult (id=🐉🐉🐉)'


def test_custom_cred_with_empty_encrypted_field():
    ct = CredentialType(name='My Custom Cred', kind='custom', inputs={'fields': [{'id': 'some_field', 'label': 'My Field', 'secret': True}]})
    cred = Credential(id=4, name='Testing 1 2 3', credential_type=ct, inputs={})
    assert cred.encrypt_field('some_field', None) is None


@pytest.mark.parametrize(
    (
        'apps',
        'app_config',
    ),
    [
        (
            apps,
            None,
        ),
        (
            None,
            apps.get_app_config('main'),
        ),
    ],
)
def test__get_credential_type_class(apps, app_config):
    ct = CredentialType._get_credential_type_class(apps=apps, app_config=app_config)
    assert ct.__name__ == 'CredentialType'


def test__get_credential_type_class_invalid_params():
    with pytest.raises(ValueError) as e:
        CredentialType._get_credential_type_class(apps=apps, app_config=apps.get_app_config('main'))

    assert type(e.value) is ValueError
    assert str(e.value) == 'Expected only apps or app_config to be defined, not both'


def test_credential_context_property():
    """Test that credential context property initializes empty dict and persists across accesses."""
    ct = CredentialType(name='Test Cred', kind='vault')
    cred = Credential(id=1, name='Test Credential', credential_type=ct, inputs={})

    # First access should return empty dict
    context = cred.context
    assert context == {}

    # Modify the context
    context['test_key'] = 'test_value'

    # Second access should return the same dict with modifications
    assert cred.context == {'test_key': 'test_value'}
    assert cred.context is context  # Same object reference


def test_credential_context_property_independent_instances():
    """Test that context property is independent between credential instances."""
    ct = CredentialType(name='Test Cred', kind='vault')
    cred1 = Credential(id=1, name='Cred 1', credential_type=ct, inputs={})
    cred2 = Credential(id=2, name='Cred 2', credential_type=ct, inputs={})

    cred1.context['key1'] = 'value1'
    cred2.context['key2'] = 'value2'

    assert cred1.context == {'key1': 'value1'}
    assert cred2.context == {'key2': 'value2'}
    assert cred1.context is not cred2.context


def test_load_plugin_passes_description():
    plugin = SimpleNamespace(name='test_plugin', inputs={'fields': []}, backend=None, plugin_description='A test plugin')
    CredentialType.load_plugin('test_ns', plugin)
    entry = ManagedCredentialType.registry['test_ns']
    assert entry.description == 'A test plugin'
    del ManagedCredentialType.registry['test_ns']


def test_load_plugin_missing_description():
    plugin = SimpleNamespace(name='test_plugin', inputs={'fields': []}, backend=None)
    CredentialType.load_plugin('test_ns', plugin)
    entry = ManagedCredentialType.registry['test_ns']
    assert entry.description == ''
    del ManagedCredentialType.registry['test_ns']


def test_get_creation_params_external_includes_description():
    cred_type = SimpleNamespace(namespace='test_ns', kind='external', name='Test', description='My description')
    params = CredentialTypeHelper.get_creation_params(cred_type)
    assert params['description'] == 'My description'


def test_get_creation_params_external_missing_description():
    cred_type = SimpleNamespace(namespace='test_ns', kind='external', name='Test')
    params = CredentialTypeHelper.get_creation_params(cred_type)
    assert params['description'] == ''


@pytest.mark.django_db
def test_setup_tower_managed_defaults_updates_description():
    registry_entry = SimpleNamespace(
        namespace='test_ns',
        kind='external',
        name='Test Plugin',
        inputs={'fields': []},
        backend=None,
        description='Updated description',
    )
    # Create an existing credential type with no description
    ct = CredentialType.objects.create(name='Test Plugin', kind='external', namespace='old_ns')
    assert ct.description == ''

    with mock.patch.dict(ManagedCredentialType.registry, {'test_ns': registry_entry}, clear=True):
        CredentialType._setup_tower_managed_defaults()

    ct.refresh_from_db()
    assert ct.description == 'Updated description'
    assert ct.namespace == 'test_ns'
