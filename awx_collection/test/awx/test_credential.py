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
def test_create_machine_credential(run_module, admin_user, organization, silence_deprecation):
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
def test_create_vault_credential(run_module, admin_user, organization, silence_deprecation):
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

    assert cred.credential_type == cred_type


@pytest.mark.django_db
def test_input_overrides_old_fields(run_module, admin_user, organization, silence_deprecation):
    # create the vault credential type
    ct = CredentialType.defaults['vault']()
    ct.save()
    result = run_module('tower_credential', dict(
        name='A Vault credential',
        organization=organization.name,
        kind='vault',
        vault_id='1234',
        inputs={'vault_id': 'asdf'},
        state='present',
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)

    cred = Credential.objects.get(name='A Vault credential')

    assert cred.inputs['vault_id'] == 'asdf'


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
    assert 'credential_type' in result['msg']
    assert 'foobar' in result['msg']
    assert 'returned 0 items, expected 1' in result['msg']


@pytest.mark.django_db
def test_make_use_of_custom_credential_type(run_module, organization, admin_user, cred_type):
    result = run_module('tower_credential', dict(
        name='Galaxy Token for Steve',
        organization=organization.name,
        credential_type=cred_type.name,
        inputs={'token': '7rEZK38DJl58A7RxA6EC7lLvUHbBQ1'}
    ), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed', False), result

    cred = Credential.objects.get(name='Galaxy Token for Steve')
    assert cred.credential_type_id == cred_type.id
    assert list(cred.inputs.keys()) == ['token']
    assert cred.inputs['token'].startswith('$encrypted$')
    assert len(cred.inputs['token']) >= len('$encrypted$') + len('7rEZK38DJl58A7RxA6EC7lLvUHbBQ1')

    assert result['name'] == "Galaxy Token for Steve"
    assert result['id'] == cred.pk


@pytest.mark.django_db
@pytest.mark.parametrize('update_secrets', [True, False])
def test_secret_field_write_twice(run_module, organization, admin_user, cred_type, update_secrets):
    val1 = '7rEZK38DJl58A7RxA6EC7lLvUHbBQ1'
    val2 = '7rEZ238DJl5837rxA6xxxlLvUHbBQ1'
    for val in (val1, val2):
        result = run_module('tower_credential', dict(
            name='Galaxy Token for Steve',
            organization=organization.name,
            credential_type=cred_type.name,
            inputs={'token': val},
            update_secrets=update_secrets
        ), admin_user)
        assert not result.get('failed', False), result.get('msg', result)

        if update_secrets:
            assert Credential.objects.get(id=result['id']).get_input('token') == val

    if update_secrets:
        assert result.get('changed'), result
    else:
        assert result.get('changed') is False, result
        assert Credential.objects.get(id=result['id']).get_input('token') == val1
