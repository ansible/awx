# -*- coding: utf-8 -*-

import pytest

from awx.main.models import Credential, CredentialType

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
