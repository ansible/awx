# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

import itertools

import pytest
from django.core.exceptions import ValidationError

from awx.main.utils import decrypt_field
from awx.main.models import Credential, CredentialType, V1Credential

from rest_framework import serializers

EXAMPLE_PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\nxyz==\n-----END PRIVATE KEY-----'
EXAMPLE_ENCRYPTED_PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nxyz==\n-----END PRIVATE KEY-----'


@pytest.mark.django_db
def test_default_cred_types():
    assert sorted(CredentialType.defaults.keys()) == [
        'aws',
        'azure_rm',
        'cloudforms',
        'gce',
        'insights',
        'net',
        'openstack',
        'rhv',
        'satellite6',
        'scm',
        'ssh',
        'tower',
        'vault',
        'vmware',
    ]
    for type_ in CredentialType.defaults.values():
        assert type_().managed_by_tower is True


@pytest.mark.django_db
@pytest.mark.parametrize('kind', ['net', 'scm', 'ssh', 'vault'])
def test_cred_type_kind_uniqueness(kind):
    """
    non-cloud credential types are exclusive_on_kind (you can only use *one* of
    them at a time)
    """
    assert CredentialType.defaults[kind]().unique_by_kind is True


@pytest.mark.django_db
def test_cloud_kind_uniqueness():
    """
    you can specify more than one cloud credential type (as long as they have
    different names so you don't e.g., use ec2 twice")
    """
    assert CredentialType.defaults['aws']().unique_by_kind is False


@pytest.mark.django_db
def test_credential_creation(organization_factory):
    org = organization_factory('test').organization
    type_ = CredentialType(
        kind='cloud',
        name='SomeCloud',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': 'Username for SomeCloud',
                'type': 'string'
            }]
        }
    )
    type_.save()

    cred = Credential(credential_type=type_, name="Bob's Credential",
                      inputs={'username': 'bob'}, organization=org)
    cred.save()
    cred.full_clean()
    assert isinstance(cred, Credential)
    assert cred.name == "Bob's Credential"
    assert cred.inputs['username'] == cred.username == 'bob'


@pytest.mark.django_db
@pytest.mark.parametrize('kind',  ['ssh', 'net', 'scm'])
@pytest.mark.parametrize('ssh_key_data, ssh_key_unlock, valid', [
    [EXAMPLE_PRIVATE_KEY, None, True],  # unencrypted key, no unlock pass
    [EXAMPLE_PRIVATE_KEY, 'super-secret', False],  # unencrypted key, unlock pass
    [EXAMPLE_ENCRYPTED_PRIVATE_KEY, 'super-secret', True],  # encrypted key, unlock pass
    [EXAMPLE_ENCRYPTED_PRIVATE_KEY, None, False],  # encrypted key, no unlock pass
    [None, None, True],  # no key, no unlock pass
    [None, 'super-secret', False],  # no key, unlock pass
    ['INVALID-KEY-DATA', None, False],  # invalid key data
    [EXAMPLE_PRIVATE_KEY.replace('=', '\u003d'), None, True],  # automatically fix JSON-encoded GCE keys
])
def test_ssh_key_data_validation(organization, kind, ssh_key_data, ssh_key_unlock, valid):
    inputs = {'username': 'joe-user'}
    if ssh_key_data:
        inputs['ssh_key_data'] = ssh_key_data
    if ssh_key_unlock:
        inputs['ssh_key_unlock'] = ssh_key_unlock
    cred_type = CredentialType.defaults[kind]()
    cred_type.save()
    cred = Credential(
        credential_type=cred_type,
        name="Best credential ever",
        inputs=inputs,
        organization=organization
    )
    cred.save()
    if valid:
        cred.full_clean()
    else:
        with pytest.raises(Exception) as e:
            cred.full_clean()
        assert e.type in (ValidationError, serializers.ValidationError)


@pytest.mark.django_db
@pytest.mark.parametrize('inputs, valid', [
    ({'vault_password': 'some-pass'}, True),
    ({}, False),
    ({'vault_password': 'dev-pass', 'vault_id': 'dev'}, True),
    ({'vault_password': 'dev-pass', 'vault_id': 'dev@prompt'}, False),  # @ not allowed
])
def test_vault_validation(organization, inputs, valid):
    cred_type = CredentialType.defaults['vault']()
    cred_type.save()
    cred = Credential(
        credential_type=cred_type,
        name="Best credential ever",
        inputs=inputs,
        organization=organization
    )
    cred.save()
    if valid:
        cred.full_clean()
    else:
        with pytest.raises(Exception) as e:
            cred.full_clean()
        assert e.type in (ValidationError, serializers.ValidationError)


@pytest.mark.django_db
@pytest.mark.parametrize('become_method, valid', zip(
    dict(V1Credential.FIELDS['become_method'].choices).keys(),
    itertools.repeat(True)
) + [('invalid-choice', False)])
def test_choices_validity(become_method, valid, organization):
    inputs = {'become_method': become_method}
    cred_type = CredentialType.defaults['ssh']()
    cred_type.save()
    cred = Credential(
        credential_type=cred_type,
        name="Best credential ever",
        inputs=inputs,
        organization=organization
    )
    cred.save()

    if valid:
        cred.full_clean()
    else:
        with pytest.raises(serializers.ValidationError) as e:
            cred.full_clean()
        assert "'%s' is not one of" % become_method in str(e)


@pytest.mark.django_db
def test_credential_encryption(organization_factory, credentialtype_ssh):
    org = organization_factory('test').organization
    cred = Credential(
        credential_type=credentialtype_ssh,
        name="Bob's Credential",
        inputs={'password': 'testing123'},
        organization=org
    )
    cred.save()

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'testing123'


@pytest.mark.django_db
def test_credential_encryption_with_ask(organization_factory, credentialtype_ssh):
    org = organization_factory('test').organization
    cred = Credential(
        credential_type=credentialtype_ssh,
        name="Bob's Credential",
        inputs={'password': 'ASK'},
        organization=org
    )
    cred.save()

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['password'] == 'ASK'


@pytest.mark.django_db
def test_credential_with_multiple_secrets(organization_factory, credentialtype_ssh):
    org = organization_factory('test').organization
    cred = Credential(
        credential_type=credentialtype_ssh,
        name="Bob's Credential",
        inputs={'ssh_key_data': 'SOMEKEY', 'ssh_key_unlock': 'testing123'},
        organization=org
    )
    cred.save()

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()

    assert cred.inputs['ssh_key_data'].startswith('$encrypted$')
    assert decrypt_field(cred, 'ssh_key_data') == 'SOMEKEY'
    assert cred.inputs['ssh_key_unlock'].startswith('$encrypted$')
    assert decrypt_field(cred, 'ssh_key_unlock') == 'testing123'


@pytest.mark.django_db
def test_credential_update(organization_factory, credentialtype_ssh):
    org = organization_factory('test').organization
    cred = Credential(
        credential_type=credentialtype_ssh,
        name="Bob's Credential",
        inputs={'password': 'testing123'},
        organization=org
    )
    cred.save()

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    cred.inputs['password'] = 'newpassword'
    cred.save()

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'newpassword'


@pytest.mark.django_db
def test_credential_update_with_prior(organization_factory, credentialtype_ssh):
    org = organization_factory('test').organization
    cred = Credential(
        credential_type=credentialtype_ssh,
        name="Bob's Credential",
        inputs={'password': 'testing123'},
        organization=org
    )
    cred.save()

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    cred.inputs['username'] = 'joe'
    cred.inputs['password'] = '$encrypted$'
    cred.save()

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['username'] == 'joe'
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'testing123'
