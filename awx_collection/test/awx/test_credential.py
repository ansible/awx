from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import Credential, CredentialType, Organization


@pytest.fixture
def cred_type():
    # Make a credential type which will be used by the credential
    ct = CredentialType.objects.create(
        name='Ansible Galaxy Token',
        inputs={
            "fields": [
                {
                    "id": "token",
                    "type": "string",
                    "secret": True,
                    "label": "Ansible Galaxy Secret Token Value"
                }
            ],
            "required": ["token"]
        },
        injectors={
            "extra_vars": {
                "galaxy_token": "{{token}}",
            }
        }
    )
    return ct


@pytest.mark.django_db
def test_create_machine_credential(run_module, admin_user, organization):
    Organization.objects.create(name='test-org')
    # create the ssh credential type
    ct = CredentialType.defaults['ssh']()
    ct.save()
    # Example from docs
    result = run_module('tower_credential', dict(
        name='Test Machine Credential',
        organization=organization.name,
        kind='ssh',
        state='present'
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    cred = Credential.objects.get(name='Test Machine Credential')
    assert cred.credential_type == ct

    assert result['name'] == "Test Machine Credential"
    assert result['id'] == cred.pk


@pytest.mark.django_db
def test_create_vault_credential(run_module, admin_user, organization):
    # https://github.com/ansible/ansible/issues/61324
    Organization.objects.create(name='test-org')
    ct = CredentialType.defaults['vault']()
    ct.save()

    result = run_module('tower_credential', dict(
        name='Test Vault Credential',
        organization=organization.name,
        kind='vault',
        vault_id='bar',
        vault_password='foobar',
        state='present'
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    cred = Credential.objects.get(name='Test Vault Credential')
    assert cred.credential_type == ct
    assert 'vault_id' in cred.inputs
    assert 'vault_password' in cred.inputs

    assert result['name'] == "Test Vault Credential"
    assert result['id'] == cred.pk


@pytest.mark.django_db
def test_create_custom_credential_type(run_module, admin_user):
    # Example from docs
    result = run_module('tower_credential_type', dict(
        name='Nexus',
        description='Credentials type for Nexus',
        kind='cloud',
        inputs={"fields": [{"id": "server", "type": "string", "default": "", "label": ""}], "required": []},
        injectors={'extra_vars': {'nexus_credential': 'test'}},
        state='present',
        validate_certs='false'
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    ct = CredentialType.objects.get(name='Nexus')

    assert result['name'] == 'Nexus'
    assert result['id'] == ct.pk

    assert ct.inputs == {"fields": [{"id": "server", "type": "string", "default": "", "label": ""}], "required": []}
    assert ct.injectors == {'extra_vars': {'nexus_credential': 'test'}}


@pytest.mark.django_db
def test_ct_precedence_over_kind(run_module, admin_user, organization, cred_type, silence_deprecation):
    result = run_module('tower_credential', dict(
        name='A credential',
        organization=organization.name,
        kind='ssh',
        credential_type=cred_type.name,
        state='present'
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    cred = Credential.objects.get(name='A credential')

    assert cred.credential_type == cred_type.name


@pytest.mark.django_db
def test_input_overrides_old_fields(run_module, admin_user, organization):
    result = run_module('tower_credential', dict(
        name='A Vault credential',
        organization=organization.name,
        kind='Vault',
        inputs={'vault_id': 'asdf'},
        vault_id='1234',
        state='present'
    ), admin_user)
    assert not result.get('failed', False), result

    cred = Credential.objects.get(name='A Vault credential')

    assert cred.inputs.vault_id == 'asdf'


@pytest.mark.django_db
def test_missing_credential_type(run_module, admin_user, organization):
    Organization.objects.create(name='test-org')
    result = run_module('tower_credential', dict(
        name='A credential',
        organization=organization.name,
        credential_type='foobar',
        state='present'
    ), admin_user)
    assert result.get('failed', False), result
    assert 'foobar was not found on the Tower server' in result['msg']


@pytest.mark.django_db
def test_make_use_of_custom_credential_type(run_module, admin_user, cred_type):
    Organization.objects.create(name='test-org')

    result = run_module('tower_credential', dict(
        name='Galaxy Token for Steve',
        organization='test-org',
        credential_type=cred_type.name,
        inputs={'token': '7rEZK38DJl58A7RxA6EC7lLvUHbBQ1'},
        state='present'
    ), admin_user)

    cred = Credential.objects.get(name='Galaxy Token for Steve')
    assert cred.credential_type_id == cred_type.id
    assert list(cred.inputs.keys()) == ['token']
    assert cred.inputs['token'].startswith('$encrypted$')
    assert len(cred.inputs['token']) >= len('$encrypted$') + len('7rEZK38DJl58A7RxA6EC7lLvUHbBQ1')

    assert result['name'] == "Galaxy Token for Steve"
    assert result['id'] == cred.pk
