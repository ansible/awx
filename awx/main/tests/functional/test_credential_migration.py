import mock
import pytest
from contextlib import contextmanager
from copy import deepcopy

from django.apps import apps

from awx.main.models import Credential, CredentialType
from awx.main.migrations._credentialtypes import migrate_to_v2_credentials
from awx.main.utils.common import decrypt_field

EXAMPLE_PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\nxyz==\n-----END PRIVATE KEY-----'

# TODO: remove this set of tests when API v1 is removed


@contextmanager
def migrate(credential, kind):
    with mock.patch.object(Credential, 'kind', kind), \
            mock.patch.object(Credential, 'objects', mock.Mock(
                get=lambda **kw: deepcopy(credential),
                all=lambda: [credential]
            )):
                class Apps(apps.__class__):
                    def get_model(self, app, model):
                        if model == 'Credential':
                            return Credential
                        return apps.get_model(app, model)
                yield
                migrate_to_v2_credentials(Apps(), None)


@pytest.mark.django_db
def test_ssh_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'ssh'):
        cred.__dict__.update({
            'username': 'bob',
            'password': 'secret',
            'ssh_key_data': EXAMPLE_PRIVATE_KEY,
            'ssh_key_unlock': 'keypass',
            'become_method': 'sudo',
            'become_username': 'superuser',
            'become_password': 'superpassword',
        })

    assert cred.credential_type.name == 'SSH'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'secret'
    assert cred.inputs['ssh_key_data'].startswith('$encrypted$')
    assert decrypt_field(cred, 'ssh_key_data') == EXAMPLE_PRIVATE_KEY
    assert cred.inputs['ssh_key_unlock'].startswith('$encrypted$')
    assert decrypt_field(cred, 'ssh_key_unlock') == 'keypass'
    assert cred.inputs['become_method'] == 'sudo'
    assert cred.inputs['become_username'] == 'superuser'
    assert cred.inputs['become_password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'become_password') == 'superpassword'
    assert Credential.objects.count() == 1


@pytest.mark.django_db
def test_scm_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'scm'):
        cred.__dict__.update({
            'username': 'bob',
            'password': 'secret',
            'ssh_key_data': EXAMPLE_PRIVATE_KEY,
            'ssh_key_unlock': 'keypass',
        })

    assert cred.credential_type.name == 'Source Control'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'secret'
    assert cred.inputs['ssh_key_data'].startswith('$encrypted$')
    assert decrypt_field(cred, 'ssh_key_data') == EXAMPLE_PRIVATE_KEY
    assert cred.inputs['ssh_key_unlock'].startswith('$encrypted$')
    assert decrypt_field(cred, 'ssh_key_unlock') == 'keypass'
    assert Credential.objects.count() == 1


@pytest.mark.django_db
def test_vault_only_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'ssh'):
        cred.__dict__.update({
            'vault_password': 'vault',
        })

    assert cred.credential_type.name == 'Vault'
    assert cred.inputs['vault_password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'vault_password') == 'vault'
    assert Credential.objects.count() == 1


@pytest.mark.django_db
def test_vault_with_ssh_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'ssh'):
        cred.__dict__.update({
            'vault_password': 'vault',
            'username': 'bob',
            'password': 'secret',
            'ssh_key_data': EXAMPLE_PRIVATE_KEY,
            'ssh_key_unlock': 'keypass',
            'become_method': 'sudo',
            'become_username': 'superuser',
            'become_password': 'superpassword',
        })
    assert Credential.objects.count() == 2

    assert Credential.objects.filter(credential_type__name='Vault').get() == cred
    assert cred.inputs.keys() == ['vault_password']
    assert cred.inputs['vault_password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'vault_password') == 'vault'

    ssh_cred = Credential.objects.filter(credential_type__name='SSH').get()
    assert sorted(ssh_cred.inputs.keys()) == sorted(CredentialType.from_v1_kind('ssh').defined_fields)
    assert ssh_cred.credential_type.name == 'SSH'
    assert ssh_cred.inputs['username'] == 'bob'
    assert ssh_cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(ssh_cred, 'password') == 'secret'
    assert ssh_cred.inputs['ssh_key_data'].startswith('$encrypted$')
    assert decrypt_field(ssh_cred, 'ssh_key_data') == EXAMPLE_PRIVATE_KEY
    assert ssh_cred.inputs['ssh_key_unlock'].startswith('$encrypted$')
    assert decrypt_field(ssh_cred, 'ssh_key_unlock') == 'keypass'
    assert ssh_cred.inputs['become_method'] == 'sudo'
    assert ssh_cred.inputs['become_username'] == 'superuser'
    assert ssh_cred.inputs['become_password'].startswith('$encrypted$')
    assert decrypt_field(ssh_cred, 'become_password') == 'superpassword'


@pytest.mark.django_db
def test_net_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'net'):
        cred.__dict__.update({
            'username': 'bob',
            'password': 'secret',
            'ssh_key_data': EXAMPLE_PRIVATE_KEY,
            'ssh_key_unlock': 'keypass',
            'authorize_password': 'authorize-secret',
        })

    assert cred.credential_type.name == 'Network'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'secret'
    assert cred.inputs['ssh_key_data'].startswith('$encrypted$')
    assert decrypt_field(cred, 'ssh_key_data') == EXAMPLE_PRIVATE_KEY
    assert cred.inputs['ssh_key_unlock'].startswith('$encrypted$')
    assert decrypt_field(cred, 'ssh_key_unlock') == 'keypass'
    assert cred.inputs['authorize_password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'authorize_password') == 'authorize-secret'
    assert Credential.objects.count() == 1


@pytest.mark.django_db
def test_aws_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'aws'):
        cred.__dict__.update({
            'username': 'bob',
            'password': 'secret',
            'security_token': 'secret-token'
        })

    assert cred.credential_type.name == 'Amazon Web Services'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'secret'
    assert cred.inputs['security_token'].startswith('$encrypted$')
    assert decrypt_field(cred, 'security_token') == 'secret-token'
    assert Credential.objects.count() == 1


@pytest.mark.django_db
def test_openstack_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'openstack'):
        cred.__dict__.update({
            'username': 'bob',
            'password': 'secret',
            'host': 'https://keystone.example.org/',
            'project': 'TENANT_ID',
        })

    assert cred.credential_type.name == 'OpenStack'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'secret'
    assert cred.inputs['host'] == 'https://keystone.example.org/'
    assert cred.inputs['project'] == 'TENANT_ID'
    assert Credential.objects.count() == 1


@pytest.mark.skip(reason="TODO: rackspace should be a custom type (we're removing official support)")
def test_rackspace():
    pass


@pytest.mark.django_db
def test_vmware_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'vmware'):
        cred.__dict__.update({
            'username': 'bob',
            'password': 'secret',
            'host': 'https://example.org/',
        })

    assert cred.credential_type.name == 'VMware vCenter'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'secret'
    assert cred.inputs['host'] == 'https://example.org/'
    assert Credential.objects.count() == 1


@pytest.mark.django_db
def test_satellite6_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'satellite6'):
        cred.__dict__.update({
            'username': 'bob',
            'password': 'secret',
            'host': 'https://example.org/',
        })

    assert cred.credential_type.name == 'Red Hat Satellite 6'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'secret'
    assert cred.inputs['host'] == 'https://example.org/'
    assert Credential.objects.count() == 1


@pytest.mark.django_db
def test_cloudforms_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'cloudforms'):
        cred.__dict__.update({
            'username': 'bob',
            'password': 'secret',
            'host': 'https://example.org/',
        })

    assert cred.credential_type.name == 'Red Hat CloudForms'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'secret'
    assert cred.inputs['host'] == 'https://example.org/'
    assert Credential.objects.count() == 1


@pytest.mark.django_db
def test_gce_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'gce'):
        cred.__dict__.update({
            'username': 'bob',
            'project': 'PROJECT-123',
            'ssh_key_data': EXAMPLE_PRIVATE_KEY
        })

    assert cred.credential_type.name == 'Google Compute Engine'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['project'] == 'PROJECT-123'
    assert cred.inputs['ssh_key_data'].startswith('$encrypted$')
    assert decrypt_field(cred, 'ssh_key_data') == EXAMPLE_PRIVATE_KEY
    assert Credential.objects.count() == 1


@pytest.mark.django_db
def test_azure_classic_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'azure'):
        cred.__dict__.update({
            'username': 'bob',
            'ssh_key_data': EXAMPLE_PRIVATE_KEY
        })

    assert cred.credential_type.name == 'Microsoft Azure Classic (deprecated)'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['ssh_key_data'].startswith('$encrypted$')
    assert decrypt_field(cred, 'ssh_key_data') == EXAMPLE_PRIVATE_KEY
    assert Credential.objects.count() == 1


@pytest.mark.django_db
def test_azure_rm_migration():
    cred = Credential(name='My Credential')
    with migrate(cred, 'azure_rm'):
        cred.__dict__.update({
            'subscription': 'some-subscription',
            'username': 'bob',
            'password': 'some-password',
            'client': 'some-client',
            'secret': 'some-secret',
            'tenant': 'some-tenant',
        })

    assert cred.credential_type.name == 'Microsoft Azure Resource Manager'
    assert cred.inputs['subscription'] == 'some-subscription'
    assert cred.inputs['username'] == 'bob'
    assert cred.inputs['password'].startswith('$encrypted$')
    assert decrypt_field(cred, 'password') == 'some-password'
    assert cred.inputs['client'] == 'some-client'
    assert cred.inputs['secret'].startswith('$encrypted$')
    assert decrypt_field(cred, 'secret') == 'some-secret'
    assert cred.inputs['tenant'] == 'some-tenant'
    assert Credential.objects.count() == 1
