# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

import pytest
from django.core.exceptions import ValidationError

from awx.main.utils.common import decrypt_field
from awx.main.models import Credential, CredentialType


@pytest.mark.django_db
def test_default_cred_types():
    assert sorted(CredentialType.defaults.keys()) == [
        'aws',
        'azure',
        'azure_rm',
        'cloudforms',
        'gce',
        'net',
        'openstack',
        'rackspace',
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
    ({'fields': [{'id': 'username', 'label': 'Username', 'type': 'string'}]}, True),
    ({'fields': [{'id': 'username', 'label': 'Username', 'help_text': 1}]}, False),
    ({'fields': [{'id': 'username', 'label': 'Username', 'help_text': 'Help Text'}]}, True),  # noqa
    ({'fields': [{'id': 'username', 'label': 'Username'}, {'id': 'username', 'label': 'Username 2'}]}, False),  # noqa
    ({'fields': [{'id': '$invalid$', 'label': 'Invalid'}]}, False),  # noqa
    ({'fields': [{'id': 'password', 'label': 'Password', 'type': 'number'}]}, True),
    ({'fields': [{'id': 'ssh_key', 'label': 'SSH Key', 'type': 'ssh_private_key'}]}, True),  # noqa
    ({'fields': [{'id': 'other', 'label': 'Other', 'type': 'boolean'}]}, False),
    ({'fields': [{'id': 'certificate', 'label': 'Cert', 'multiline': True}]}, True),
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
        with pytest.raises(ValidationError):
            type_.full_clean()
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
def test_credential_creation_validation_failure(organization_factory):
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

    with pytest.raises(ValidationError):
        cred = Credential(credential_type=type_, name="Bob's Credential",
                          inputs={'user': 'wrong-key'}, organization=org)
        cred.save()
        cred.full_clean()


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
