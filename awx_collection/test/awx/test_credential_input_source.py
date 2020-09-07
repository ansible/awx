from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import CredentialInputSource, Credential, CredentialType, Organization


@pytest.fixture
def aim_cred_type():
    ct = CredentialType.defaults['aim']()
    ct.save()
    return ct


# Test CyberArk AIM credential source
@pytest.fixture
def source_cred_aim(aim_cred_type):
    return Credential.objects.create(
        name='CyberArk AIM Cred',
        credential_type=aim_cred_type,
        inputs={
            "url": "https://cyberark.example.com",
            "app_id": "myAppID",
            "verify": "false"
        }
    )


@pytest.mark.django_db
def test_aim_credential_source(run_module, admin_user, organization, source_cred_aim, silence_deprecation):
    ct = CredentialType.defaults['ssh']()
    ct.save()
    tgt_cred = Credential.objects.create(
        name='Test Machine Credential',
        organization=organization,
        credential_type=ct,
        inputs={'username': 'bob'}
    )

    result = run_module('tower_credential_input_source', dict(
        source_credential=source_cred_aim.name,
        target_credential=tgt_cred.name,
        input_field_name='password',
        metadata={"object_query": "Safe=SUPERSAFE;Object=MyAccount"},
        state='present'
    ), admin_user)

    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    assert CredentialInputSource.objects.count() == 1
    cis = CredentialInputSource.objects.first()

    assert cis.metadata['object_query'] == "Safe=SUPERSAFE;Object=MyAccount"
    assert cis.source_credential.name == source_cred_aim.name
    assert cis.target_credential.name == tgt_cred.name
    assert cis.input_field_name == 'password'
    assert result['id'] == cis.pk


# Test CyberArk Conjur credential source
@pytest.fixture
def source_cred_conjur(organization):
    # Make a credential type which will be used by the credential
    ct = CredentialType.defaults['conjur']()
    ct.save()
    return Credential.objects.create(
        name='CyberArk CONJUR Cred',
        credential_type=ct,
        inputs={
            "url": "https://cyberark.example.com",
            "api_key": "myApiKey",
            "account": "account",
            "username": "username"
        }
    )


@pytest.mark.django_db
def test_conjur_credential_source(run_module, admin_user, organization, source_cred_conjur, silence_deprecation):
    ct = CredentialType.defaults['ssh']()
    ct.save()
    tgt_cred = Credential.objects.create(
        name='Test Machine Credential',
        organization=organization,
        credential_type=ct,
        inputs={'username': 'bob'}
    )

    result = run_module('tower_credential_input_source', dict(
        source_credential=source_cred_conjur.name,
        target_credential=tgt_cred.name,
        input_field_name='password',
        metadata={"secret_path": "/path/to/secret"},
        state='present'
    ), admin_user)

    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    assert CredentialInputSource.objects.count() == 1
    cis = CredentialInputSource.objects.first()

    assert cis.metadata['secret_path'] == "/path/to/secret"
    assert cis.source_credential.name == source_cred_conjur.name
    assert cis.target_credential.name == tgt_cred.name
    assert cis.input_field_name == 'password'
    assert result['id'] == cis.pk


# Test Hashicorp Vault secret credential source
@pytest.fixture
def source_cred_hashi_secret(organization):
    # Make a credential type which will be used by the credential
    ct = CredentialType.defaults['hashivault_kv']()
    ct.save()
    return Credential.objects.create(
        name='HashiCorp secret Cred',
        credential_type=ct,
        inputs={
            "url": "https://secret.hash.example.com",
            "token": "myApiKey",
            "role_id": "role",
            "secret_id": "secret",
            "default_auth_path": "path-to-approle"
        }
    )


@pytest.mark.django_db
def test_hashi_secret_credential_source(run_module, admin_user, organization, source_cred_hashi_secret, silence_deprecation):
    ct = CredentialType.defaults['ssh']()
    ct.save()
    tgt_cred = Credential.objects.create(
        name='Test Machine Credential',
        organization=organization,
        credential_type=ct,
        inputs={'username': 'bob'}
    )

    result = run_module('tower_credential_input_source', dict(
        source_credential=source_cred_hashi_secret.name,
        target_credential=tgt_cred.name,
        input_field_name='password',
        metadata={"secret_path": "/path/to/secret", "auth_path": "/path/to/auth", "secret_backend": "backend", "secret_key": "a_key"},
        state='present'
    ), admin_user)

    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    assert CredentialInputSource.objects.count() == 1
    cis = CredentialInputSource.objects.first()

    assert cis.metadata['secret_path'] == "/path/to/secret"
    assert cis.metadata['auth_path'] == "/path/to/auth"
    assert cis.metadata['secret_backend'] == "backend"
    assert cis.metadata['secret_key'] == "a_key"
    assert cis.source_credential.name == source_cred_hashi_secret.name
    assert cis.target_credential.name == tgt_cred.name
    assert cis.input_field_name == 'password'
    assert result['id'] == cis.pk


# Test Hashicorp Vault signed ssh credential source
@pytest.fixture
def source_cred_hashi_ssh(organization):
    # Make a credential type which will be used by the credential
    ct = CredentialType.defaults['hashivault_ssh']()
    ct.save()
    return Credential.objects.create(
        name='HashiCorp ssh Cred',
        credential_type=ct,
        inputs={
            "url": "https://ssh.hash.example.com",
            "token": "myApiKey",
            "role_id": "role",
            "secret_id": "secret"
        }
    )


@pytest.mark.django_db
def test_hashi_ssh_credential_source(run_module, admin_user, organization, source_cred_hashi_ssh, silence_deprecation):
    ct = CredentialType.defaults['ssh']()
    ct.save()
    tgt_cred = Credential.objects.create(
        name='Test Machine Credential',
        organization=organization,
        credential_type=ct,
        inputs={'username': 'bob'}
    )

    result = run_module('tower_credential_input_source', dict(
        source_credential=source_cred_hashi_ssh.name,
        target_credential=tgt_cred.name,
        input_field_name='password',
        metadata={"secret_path": "/path/to/secret", "auth_path": "/path/to/auth", "role": "role", "public_key": "a_key", "valid_principals": "some_value"},
        state='present'
    ), admin_user)

    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    assert CredentialInputSource.objects.count() == 1
    cis = CredentialInputSource.objects.first()

    assert cis.metadata['secret_path'] == "/path/to/secret"
    assert cis.metadata['auth_path'] == "/path/to/auth"
    assert cis.metadata['role'] == "role"
    assert cis.metadata['public_key'] == "a_key"
    assert cis.metadata['valid_principals'] == "some_value"
    assert cis.source_credential.name == source_cred_hashi_ssh.name
    assert cis.target_credential.name == tgt_cred.name
    assert cis.input_field_name == 'password'
    assert result['id'] == cis.pk


# Test Azure Key Vault credential source
@pytest.fixture
def source_cred_azure_kv(organization):
    # Make a credential type which will be used by the credential
    ct = CredentialType.defaults['azure_kv']()
    ct.save()
    return Credential.objects.create(
        name='Azure KV Cred',
        credential_type=ct,
        inputs={
            "url": "https://key.azure.example.com",
            "client": "client",
            "secret": "secret",
            "tenant": "tenant",
            "cloud_name": "the_cloud",
        }
    )


@pytest.mark.django_db
def test_azure_kv_credential_source(run_module, admin_user, organization, source_cred_azure_kv, silence_deprecation):
    ct = CredentialType.defaults['ssh']()
    ct.save()
    tgt_cred = Credential.objects.create(
        name='Test Machine Credential',
        organization=organization,
        credential_type=ct,
        inputs={'username': 'bob'}
    )

    result = run_module('tower_credential_input_source', dict(
        source_credential=source_cred_azure_kv.name,
        target_credential=tgt_cred.name,
        input_field_name='password',
        metadata={"secret_field": "my_pass"},
        state='present'
    ), admin_user)

    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    assert CredentialInputSource.objects.count() == 1
    cis = CredentialInputSource.objects.first()

    assert cis.metadata['secret_field'] == "my_pass"
    assert cis.source_credential.name == source_cred_azure_kv.name
    assert cis.target_credential.name == tgt_cred.name
    assert cis.input_field_name == 'password'
    assert result['id'] == cis.pk


# Test Changing Credential Source
@pytest.fixture
def source_cred_aim_alt(aim_cred_type):
    return Credential.objects.create(
        name='Alternate CyberArk AIM Cred',
        credential_type=aim_cred_type,
        inputs={
            "url": "https://cyberark-alt.example.com",
            "app_id": "myAltID",
            "verify": "false"
        }
    )


@pytest.mark.django_db
def test_aim_credential_source(run_module, admin_user, organization, source_cred_aim, source_cred_aim_alt, silence_deprecation):
    ct = CredentialType.defaults['ssh']()
    ct.save()
    tgt_cred = Credential.objects.create(
        name='Test Machine Credential',
        organization=organization,
        credential_type=ct,
        inputs={'username': 'bob'}
    )

    result = run_module('tower_credential_input_source', dict(
        source_credential=source_cred_aim.name,
        target_credential=tgt_cred.name,
        input_field_name='password',
        metadata={"object_query": "Safe=SUPERSAFE;Object=MyAccount"},
        state='present'
    ), admin_user)

    assert not result.get('failed', False), result.get('msg', result)
    assert result.get('changed'), result

    unchangedResult = run_module('tower_credential_input_source', dict(
        source_credential=source_cred_aim.name,
        target_credential=tgt_cred.name,
        input_field_name='password',
        metadata={"object_query": "Safe=SUPERSAFE;Object=MyAccount"},
        state='present'
    ), admin_user)

    assert not unchangedResult.get('failed', False), result.get('msg', result)
    assert not unchangedResult.get('changed'), result

    changedResult = run_module('tower_credential_input_source', dict(
        source_credential=source_cred_aim_alt.name,
        target_credential=tgt_cred.name,
        input_field_name='password',
        state='present'
    ), admin_user)

    assert not changedResult.get('failed', False), changedResult.get('msg', result)
    assert changedResult.get('changed'), result

    assert CredentialInputSource.objects.count() == 1
    cis = CredentialInputSource.objects.first()

    assert cis.metadata['object_query'] == "Safe=SUPERSAFE;Object=MyAccount"
    assert cis.source_credential.name == source_cred_aim_alt.name
    assert cis.target_credential.name == tgt_cred.name
    assert cis.input_field_name == 'password'
