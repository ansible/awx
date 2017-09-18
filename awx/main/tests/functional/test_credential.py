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
        'satellite6',
        'scm',
        'ssh',
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
@pytest.mark.parametrize('input_, valid', [
    ({}, True),
    ({'fields': []}, True),
    ({'fields': {}}, False),
    ({'fields': 123}, False),
    ({'fields': [{'id': 'username', 'label': 'Username', 'foo': 'bar'}]}, False),
    ({'fields': [{'id': 'username', 'label': 'Username'}]}, True),
    ({'fields': [{'id': 'username', 'label': 'Username', 'type': 'string'}]}, True),
    ({'fields': [{'id': 'username', 'label': 'Username', 'help_text': 1}]}, False),
    ({'fields': [{'id': 'username', 'label': 'Username', 'help_text': 'Help Text'}]}, True),  # noqa
    ({'fields': [{'id': 'username', 'label': 'Username'}, {'id': 'username', 'label': 'Username 2'}]}, False),  # noqa
    ({'fields': [{'id': '$invalid$', 'label': 'Invalid', 'type': 'string'}]}, False),  # noqa
    ({'fields': [{'id': 'password', 'label': 'Password', 'type': 'invalid-type'}]}, False),
    ({'fields': [{'id': 'ssh_key', 'label': 'SSH Key', 'type': 'string', 'format': 'ssh_private_key'}]}, True),  # noqa
    ({'fields': [{'id': 'flag', 'label': 'Some Flag', 'type': 'boolean'}]}, True),
    ({'fields': [{'id': 'flag', 'label': 'Some Flag', 'type': 'boolean', 'choices': ['a', 'b']}]}, False),
    ({'fields': [{'id': 'flag', 'label': 'Some Flag', 'type': 'boolean', 'secret': True}]}, False),
    ({'fields': [{'id': 'certificate', 'label': 'Cert', 'multiline': True}]}, True),
    ({'fields': [{'id': 'certificate', 'label': 'Cert', 'multiline': True, 'type': 'boolean'}]}, False),  # noqa
    ({'fields': [{'id': 'certificate', 'label': 'Cert', 'multiline': 'bad'}]}, False),  # noqa
    ({'fields': [{'id': 'token', 'label': 'Token', 'secret': True}]}, True),
    ({'fields': [{'id': 'token', 'label': 'Token', 'secret': 'bad'}]}, False),
    ({'fields': [{'id': 'token', 'label': 'Token', 'ask_at_runtime': True}]}, True),
    ({'fields': [{'id': 'token', 'label': 'Token', 'ask_at_runtime': 'bad'}]}, False),  # noqa
    ({'fields': [{'id': 'become_method', 'label': 'Become', 'choices': 'not-a-list'}]}, False),  # noqa
    ({'fields': [{'id': 'become_method', 'label': 'Become', 'choices': []}]}, False),
    ({'fields': [{'id': 'become_method', 'label': 'Become', 'choices': ['su', 'sudo']}]}, True),  # noqa
    ({'fields': [{'id': 'become_method', 'label': 'Become', 'choices': ['dup', 'dup']}]}, False),  # noqa
    ({'fields': [{'id': 'tower', 'label': 'Reserved!', }]}, False),  # noqa
])
def test_cred_type_input_schema_validity(input_, valid):
    type_ = CredentialType(
        kind='cloud',
        name='SomeCloud',
        managed_by_tower=True,
        inputs=input_
    )
    if valid is False:
        with pytest.raises(Exception) as e:
            type_.full_clean()
        assert e.type in (ValidationError, serializers.ValidationError)
    else:
        type_.full_clean()


@pytest.mark.django_db
@pytest.mark.parametrize('injectors, valid', [
    ({}, True),
    ({'invalid-injector': {}}, False),
    ({'file': 123}, False),
    ({'file': {}}, False),
    ({'file': {'template': '{{username}}'}}, True),
    ({'file': {'foo': 'bar'}}, False),
    ({'env': 123}, False),
    ({'env': {}}, True),
    ({'env': {'AWX_SECRET': '{{awx_secret}}'}}, True),
    ({'env': {'AWX_SECRET_99': '{{awx_secret}}'}}, True),
    ({'env': {'99': '{{awx_secret}}'}}, False),
    ({'env': {'AWX_SECRET=': '{{awx_secret}}'}}, False),
    ({'extra_vars': 123}, False),
    ({'extra_vars': {}}, True),
    ({'extra_vars': {'hostname': '{{host}}'}}, True),
    ({'extra_vars': {'hostname_99': '{{host}}'}}, True),
    ({'extra_vars': {'99': '{{host}}'}}, False),
    ({'extra_vars': {'99=': '{{host}}'}}, False),
])
def test_cred_type_injectors_schema(injectors, valid):
    type_ = CredentialType(
        kind='cloud',
        name='SomeCloud',
        managed_by_tower=True,
        inputs={
            'fields': [
                {'id': 'username', 'type': 'string', 'label': '_'},
                {'id': 'pass', 'type': 'string', 'label': '_'},
                {'id': 'awx_secret', 'type': 'string', 'label': '_'},
                {'id': 'host', 'type': 'string', 'label': '_'},
            ]
        },
        injectors=injectors
    )
    if valid is False:
        with pytest.raises(ValidationError):
            type_.full_clean()
    else:
        type_.full_clean()


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
@pytest.mark.parametrize('inputs', [
    ['must-be-a-dict'],
    {'user': 'wrong-key'},
    {'username': 1},
    {'username': 1.5},
    {'username': ['a', 'b', 'c']},
    {'username': {'a': 'b'}},
    {'username': False},
    {'flag': 1},
    {'flag': 1.5},
    {'flag': ['a', 'b', 'c']},
    {'flag': {'a': 'b'}},
    {'flag': 'some-string'},
])
def test_credential_creation_validation_failure(organization_factory, inputs):
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
            },{
                'id': 'flag',
                'label': 'Some Boolean Flag',
                'type': 'boolean'
            }]
        }
    )
    type_.save()

    with pytest.raises(Exception) as e:
        cred = Credential(credential_type=type_, name="Bob's Credential",
                          inputs=inputs, organization=org)
        cred.save()
        cred.full_clean()
        assert e.type in (ValidationError, serializers.ValidationError)


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
