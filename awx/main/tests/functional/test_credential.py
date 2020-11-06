# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

import pytest
from django.core.exceptions import ValidationError

from awx.main.utils import decrypt_field
from awx.main.models import Credential, CredentialType

from rest_framework import serializers

EXAMPLE_PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\nxyz==\n-----END PRIVATE KEY-----'
EXAMPLE_ENCRYPTED_PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nxyz==\n-----END PRIVATE KEY-----'

PKCS8_PRIVATE_KEY = '''-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQD0uyqyUHELQ25B
8lNBu/ZfVx8fPFT6jvAUscxfWLqsZCJrR8BWadXMa/0ALMaUuZbZ8Ug27jztOSO8
w8hJ6dqHaQ2gfbwsfbF6XHaetap0OoAFtnaiULSvljOkoWG+WSyfvJ73ZwEP3KzW
0JbNX24zGFdTFzX1W+8BbLpEIw3XiP9iYPtu0uit6VradMrt2Kdu+VKlQzbG1+89
g70IyFkvopynnWAkA+YXNo08dxOzmci7/G0Cp1Lwh4IAH++HbE2E4odWm5zoCaT7
gcZzKuZs/kkDHaS9O5VjsWGrZ+mp3NgeABbFRP0jDhCtS8QRa94RC6mobtnYoRd7
C1Iz3cdjAgMBAAECggEAb5p9BZUegBrviH5YDmWHnIHP7QAn5p1RibZtM1v0wRHn
ClJNuXqJJ7BlT3Ob2Y3q55ebLYWmXi4NCJOl3mMZJ2A2eSZtrkJhsaHB7G1+/oMB
B9nmLu4r/9i4005PEy16ZpvvSHZ+KvwhC9NSufRXflCO3hL7JdmXXGh3ZwQvV0a7
mP1RIQKIcLynPBTbTH1w30Znj2M4bSjUlsLbOYhwg2YQxa1qKuCtata5qdAVbgny
JYPruBhcHLPGvC0FBcd8zoYWLvQ52hcXNxrl0iN1KY7zIEYmU+3gbuBIoVl2Qo/p
zmH01bo9h9p5DdkjQ6MdjvrOX8aT93S1g9y8WqtoXQKBgQD7E2+RZ/XNIFts9cqG
2S7aywIydkgEmaOJl1fzebutJPPQXJDpQZtEenr+CG7KsRPf8nJ3jc/4OHIsnHYD
WBgXLQz0QWEgXwTRicXsxsARzHKV2Lb8IsXK5vfia+i9fxZV3WwkKVXOmTJHcVl1
XD5zfbAlrQ4r+Uo618zgpchsBQKBgQD5h+A+PX+3PdUPNkHdCltMwaSsXjBcYYoF
uZGR4v8jRQguGD5h8Eyk/cS3VVryYRKiYJCvaPFXTzN6GAsQoSnMW+37GKsbL+oK
5JYoSiCY6BpaJO3uo/UwvitV8EjHdaArb5oBjx1yiobRqhVJ+iH1PKxgnQFI5RgO
4AhnnYMqRwKBgQDUX+VQXlp5LzSGXwX3uH+8jFmIa6qRUZAWU1EO3tqUI5ykk5fz
5g27B8s/U8y7YLuKA581Z1wR/1T8TUA5peuCtxWtChxo8Fa4E0y68ocGxyPpgk2N
yq/56BKnkFVm7Lfs24WctOYjAkyYR9W+ws8Ei71SsSY6pfxW97ESGMkGLQKBgAlW
ABnUCzc75QDQst4mSQwyIosgawbJz3QvYTboG0uihY/T8GGRsAxsQjPpyaFP6HaS
zlcBwiXWHMLwq1lP7lRrDBhc7+nwfP0zWDrhqx6NcI722sAW+lF8i/qHJvHvgLKf
Vk/AnwVuEWU+y9UcurCGOJzUwvuLNr83upjF1+Z5AoGAP91XiBCorJLRJaryi6zt
iCjRxoVsrN6NvAh+MQ1yfAopO4RhxEXM/uUOBkulNhlnp+evSxUwDnFNOWzsZVn9
B6yXdJ9BTWXFX7YhEkosRZCXnNWX4Dz+DGU/yvSHQR/JYj8mRav98TmJU6lK6Vw/
YukmWPxNB+x4Ym3RNPrLpU4=
-----END PRIVATE KEY-----'''
PKCS8_ENCRYPTED_PRIVATE_KEY = '''-----BEGIN ENCRYPTED PRIVATE KEY-----
MIIFHzBJBgkqhkiG9w0BBQ0wPDAbBgkqhkiG9w0BBQwwDgQIC4E/DX+33rACAggA
MB0GCWCGSAFlAwQBAgQQbeAsQdsEKoztekP5JXmHFASCBNAmNAMGSnycmN4sYleT
NS9r/ph9v58dv0/hzbE6TCt/i6nmA/D8mtuYB8gm30E/DOuN/dnL3z2gpyvr478P
FjoRnueuwMdLcfEpzEXotJdc7vmUsSjTFq99oh84JHdCfWSRtxkDu64dwp3GPC9+
f1qqg6o4/bPkjni+bCMgq9vgr4K+vuaKzaJqUTEQFuT3CirDGoWGpfRDtDoBmlg8
8esEXoA6RD2DNv6fQrOu9Q4Fc0YkzcoIfY6EJxu+f75LF/NUVpmeJ8QDjj6VFVuX
35ChPYolhBSC/MHBHAVVrn17FAdpLkiz7hIR7KBIg2nuu8oUnPMzDff/CeehYzNb
OH12P9zaHZa3DZHuu27oI6yUdgs8HYNLtBzXH/DbyAeW9alg1Ofber5DO62ieL3E
LqBd4R7qqDSTQmiA6B8LkVIrFrIOqn+nWoM9gHhIrTI409A/oTbpen87sZ4MIQk4
Vjw/A/D5OYhnjOEVgMXrNpKzFfRJPdKh8LYjAaytsLKZk/NOWKpBOcIPhBG/agmx
CX2NE2tpwNo+uWSOG6qTqc8xiQFDsQmbz9YEuux13J3Hg5gVMOJQNMvYpxgFD156
Z82QBMdrY1tRIA91kW97UDj6OEAyz8HnmL+rCiRLGJXKUnZsSET+VHs9+uhBggX8
GxliP35pYlmdejqGWHjiYlGF2+WKrd5axx/m1DcfZdXSaF1IdLKafnNXzUZbOnOM
7RbKHDhBKr/vkBV1SGYgDLNn4hflFzhdI65AKxO2KankzaWxF09/0kRZlmxm+tZX
8r0fHe9IO1KQR/52Kfg1vAQdt2KiyAziw5+tcqQT28knSDboNKpD2Du8BAoH9xG7
0Ca57oBHh/VGzM/niJBjI4EMOPZKuRJsxZF7wOOO6NTh/XFf3LpzsR1y3qoXN4cR
n+/jLUO/3kSGsqso6DT9C0o1pTrnORaJb4aF05jljFx9LYiQUOoLujp8cVW7XxQB
pTgJEFxTN5YA//cwYu3GOJ1AggSeF/WkHCDfCTpTfnO/WTZ0oc+nNyC1lBVfcZ67
GCH8COsfmhusrYiJUN6vYZIr4MfylVg53PUKYbLKYad9bIIaYYuu3MP4CtKDWHvk
8q+GzpjVUCPwjjsea56RMav+xDPvmgIayDptae26Fv+mRPcwqORYMFNtVRG6DUXo
+lrWlaDlkfyfZlQ6sK5c1cJNI8pSPocP/c9TBhP+xFROiWxvMOxhM7DmDl8rhAxU
ttZSukCg7n38AFsUqg5eLLq9sT+P6VmX8d3YflPBIkvNgK7nKUTwgrpbuADo07b0
sVlAY/9SmtHvOCibxphvPYUOhwWo97PzzAsdVGz/xRvH8mzI/Iftbc1U2C2La8FJ
xjaAFwWK/CjQSwnCB8raWo9FUavV6xdb2K0G4VBVDvZO9EJBzX0m6EqQx3XMZf1s
crP0Dp9Ee66vVOlj+XnyyTkUADSYHr8/42Aohv96fJEMjy5gbBl4QQm2QKzAkq9n
lrHvQpCxPixUUAEI0ZL1Y74hcMecnfbpGibrUvSp+cyDCOG92KKxLXEgVYCbXHZu
bOlOanZF3vC6I9dUC2d8I5B87b2K+y57OkWpmS3zxCEpsBqQmn8Te50DnlkPJPBj
GLqbpJyX2r3p/Rmo6mLY71SqpA==
-----END ENCRYPTED PRIVATE KEY-----'''


@pytest.mark.django_db
def test_default_cred_types():
    assert sorted(CredentialType.defaults.keys()) == [
        'aim',
        'aws',
        'azure_kv',
        'azure_rm',
        'conjur',
        'galaxy_api_token',
        'gce',
        'github_token',
        'gitlab_token',
        'hashivault_kv',
        'hashivault_ssh',
        'insights',
        'kubernetes_bearer_token',
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
    assert cred.inputs['username'] == 'bob'


@pytest.mark.django_db
@pytest.mark.parametrize('kind',  ['ssh', 'net', 'scm'])
@pytest.mark.parametrize('ssh_key_data, ssh_key_unlock, valid', [
    [EXAMPLE_PRIVATE_KEY, None, True],  # unencrypted key, no unlock pass
    [EXAMPLE_PRIVATE_KEY, 'super-secret', False],  # unencrypted key, unlock pass
    [EXAMPLE_ENCRYPTED_PRIVATE_KEY, 'super-secret', True],  # encrypted key, unlock pass
    [EXAMPLE_ENCRYPTED_PRIVATE_KEY, None, False],  # encrypted key, no unlock pass
    [PKCS8_ENCRYPTED_PRIVATE_KEY, 'passme', True],  # encrypted PKCS8 key, unlock pass
    [PKCS8_ENCRYPTED_PRIVATE_KEY, None, False],  # encrypted PKCS8 key, no unlock pass
    [PKCS8_PRIVATE_KEY, None, True],  # unencrypted PKCS8 key, no unlock pass
    [PKCS8_PRIVATE_KEY, 'passme', False],  # unencrypted PKCS8 key, unlock pass
    [None, None, True],  # no key, no unlock pass
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
    ({}, True),
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
@pytest.mark.parametrize('become_method, valid', [
    ('', True),
    ('sudo', True),
    ('custom-plugin', True),
])
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


@pytest.mark.django_db
def test_credential_get_input(organization_factory):
    organization = organization_factory('test').organization
    type_ = CredentialType(
        kind='vault',
        name='somevault',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'vault_password',
                'type': 'string',
                'secret': True,
            }, {
                'id': 'vault_id',
                'type': 'string',
                'secret': False
            }, {
                'id': 'secret',
                'type': 'string',
                'secret': True,
            }]
        }
    )
    type_.save()

    cred = Credential(
        organization=organization,
        credential_type=type_,
        name="Bob's Credential",
        inputs={'vault_password': 'testing321'}
    )
    cred.save()
    cred.full_clean()

    assert isinstance(cred, Credential)
    # verify expected exception is raised when attempting to access an unset
    # input without providing a default
    with pytest.raises(AttributeError):
        cred.get_input('vault_id')
    # verify that the provided default is used for unset inputs
    assert cred.get_input('vault_id', default='foo') == 'foo'
    # verify expected exception is raised when attempting to access an undefined
    # input without providing a default
    with pytest.raises(AttributeError):
        cred.get_input('field_not_on_credential_type')
    # verify that the provided default is used for undefined inputs
    assert cred.get_input('field_not_on_credential_type', default='bar') == 'bar'
    # verify expected exception is raised when attempting to access an unset secret
    # input without providing a default
    with pytest.raises(AttributeError):
        cred.get_input('secret')
    # verify that the provided default is used for undefined inputs
    assert cred.get_input('secret', default='fiz') == 'fiz'
    # verify return values for encrypted secret fields are decrypted
    assert cred.inputs['vault_password'].startswith('$encrypted$')
    assert cred.get_input('vault_password') == 'testing321'
