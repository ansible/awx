import itertools
import re

from unittest import mock # noqa
import pytest

from django.utils.encoding import smart_str

from awx.main.models import (AdHocCommand, Credential, CredentialType, Job, JobTemplate,
                             Inventory, InventorySource, Project,
                             WorkflowJobNode)
from awx.main.utils import decrypt_field
from awx.api.versioning import reverse

EXAMPLE_PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\nxyz==\n-----END PRIVATE KEY-----'
EXAMPLE_ENCRYPTED_PRIVATE_KEY = '-----BEGIN PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nxyz==\n-----END PRIVATE KEY-----'


@pytest.mark.django_db
def test_idempotent_credential_type_setup():
    assert CredentialType.objects.count() == 0
    CredentialType.setup_tower_managed_defaults()
    total = CredentialType.objects.count()
    assert total > 0

    CredentialType.setup_tower_managed_defaults()
    assert CredentialType.objects.count() == total


@pytest.mark.django_db
@pytest.mark.parametrize('kind, total', [
    ('ssh', 1), ('net', 0)
])
def test_filter_by_v1_kind(get, admin, organization, kind, total):
    CredentialType.setup_tower_managed_defaults()
    cred = Credential(
        credential_type=CredentialType.from_v1_kind('ssh'),
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'jim',
            'password': u'secret'
        }
    )
    cred.save()

    response = get(
        reverse('api:credential_list', kwargs={'version': 'v1'}),
        admin,
        QUERY_STRING='kind=%s' % kind
    )
    assert response.status_code == 200
    assert response.data['count'] == total


@pytest.mark.django_db
def test_filter_by_v1_kind_with_vault(get, admin, organization):
    CredentialType.setup_tower_managed_defaults()
    cred = Credential(
        credential_type=CredentialType.objects.get(kind='ssh'),
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'jim',
            'password': u'secret'
        }
    )
    cred.save()
    cred = Credential(
        credential_type=CredentialType.objects.get(kind='vault'),
        name='Best credential ever',
        organization=organization,
        inputs={
            'vault_password': u'vault!'
        }
    )
    cred.save()

    response = get(
        reverse('api:credential_list', kwargs={'version': 'v1'}),
        admin,
        QUERY_STRING='kind=ssh'
    )
    assert response.status_code == 200
    assert response.data['count'] == 2


@pytest.mark.django_db
def test_insights_credentials_in_v1_api_list(get, admin, organization):
    credential_type = CredentialType.defaults['insights']()
    credential_type.save()
    cred = Credential(
        credential_type=credential_type,
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'joe',
            'password': u'secret'
        }
    )
    cred.save()

    response = get(
        reverse('api:credential_list', kwargs={'version': 'v1'}),
        admin
    )
    assert response.status_code == 200
    assert response.data['count'] == 1
    cred = response.data['results'][0]
    assert cred['kind'] == 'insights'
    assert cred['username'] == 'joe'
    assert cred['password'] == '$encrypted$'


@pytest.mark.django_db
def test_create_insights_credentials_in_v1(get, post, admin, organization):
    credential_type = CredentialType.defaults['insights']()
    credential_type.save()

    response = post(
        reverse('api:credential_list', kwargs={'version': 'v1'}),
        {
            'name': 'Best Credential Ever',
            'organization': organization.id,
            'kind': 'insights',
            'username': 'joe',
            'password': 'secret'
        },
        admin
    )
    assert response.status_code == 201
    cred = Credential.objects.get(pk=response.data['id'])
    assert cred.username == 'joe'
    assert decrypt_field(cred, 'password') == 'secret'
    assert cred.credential_type == credential_type


@pytest.mark.django_db
def test_custom_credentials_not_in_v1_api_list(get, admin, organization):
    """
    'Custom' credentials (those not managed by Tower) shouldn't be visible from
    the V1 credentials API list
    """
    credential_type = CredentialType(
        kind='cloud',
        name='MyCloud',
        inputs = {
            'fields': [{
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True
            }]
        }
    )
    credential_type.save()
    cred = Credential(
        credential_type=credential_type,
        name='Best credential ever',
        organization=organization,
        inputs={
            'password': u'secret'
        }
    )
    cred.save()

    response = get(
        reverse('api:credential_list', kwargs={'version': 'v1'}),
        admin
    )
    assert response.status_code == 200
    assert response.data['count'] == 0


@pytest.mark.django_db
def test_custom_credentials_not_in_v1_api_detail(get, admin, organization):
    """
    'Custom' credentials (those not managed by Tower) shouldn't be visible from
    the V1 credentials API detail
    """
    credential_type = CredentialType(
        kind='cloud',
        name='MyCloud',
        inputs = {
            'fields': [{
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True
            }]
        }
    )
    credential_type.save()
    cred = Credential(
        credential_type=credential_type,
        name='Best credential ever',
        organization=organization,
        inputs={
            'password': u'secret'
        }
    )
    cred.save()

    response = get(
        reverse('api:credential_detail', kwargs={'version': 'v1', 'pk': cred.pk}),
        admin
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_filter_by_v1_invalid_kind(get, admin, organization):
    response = get(
        reverse('api:credential_list', kwargs={'version': 'v1'}),
        admin,
        QUERY_STRING='kind=bad_kind'
    )
    assert response.status_code == 400


#
# user credential creation
#


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_create_user_credential_via_credentials_list(post, get, alice, credentialtype_ssh, version, params):
    params['user'] = alice.id
    params['name'] = 'Some name'
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        alice
    )
    assert response.status_code == 201

    response = get(reverse('api:credential_list', kwargs={'version': version}), alice)
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_credential_validation_error_with_bad_user(post, admin, version, credentialtype_ssh, params):
    params['user'] = 'asdf'
    params['name'] = 'Some name'
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 400
    assert response.data['user'][0] == 'Incorrect type. Expected pk value, received str.'


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_create_user_credential_via_user_credentials_list(post, get, alice, credentialtype_ssh, version, params):
    params['user'] = alice.id
    params['name'] = 'Some name'
    response = post(
        reverse('api:user_credentials_list', kwargs={'version': version, 'pk': alice.pk}),
        params,
        alice
    )
    assert response.status_code == 201

    response = get(reverse('api:user_credentials_list', kwargs={'version': version, 'pk': alice.pk}), alice)
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_create_user_credential_via_credentials_list_xfail(post, alice, bob, version, params):
    params['user'] = bob.id
    params['name'] = 'Some name'
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        alice
    )
    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_create_user_credential_via_user_credentials_list_xfail(post, alice, bob, version, params):
    params['user'] = bob.id
    params['name'] = 'Some name'
    response = post(
        reverse('api:user_credentials_list', kwargs={'version': version, 'pk': bob.pk}),
        params,
        alice
    )
    assert response.status_code == 403


#
# team credential creation
#


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_create_team_credential(post, get, team, organization, org_admin, team_member, credentialtype_ssh, version, params):
    params['team'] = team.id
    params['name'] = 'Some name'
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        org_admin
    )
    assert response.status_code == 201

    response = get(
        reverse('api:team_credentials_list', kwargs={'version': version, 'pk': team.pk}),
        team_member
    )
    assert response.status_code == 200
    assert response.data['count'] == 1

    # Assure that credential's organization is implictly set to team's org
    assert response.data['results'][0]['summary_fields']['organization']['id'] == team.organization.id


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_create_team_credential_via_team_credentials_list(post, get, team, org_admin, team_member, credentialtype_ssh, version, params):
    params['team'] = team.id
    params['name'] = 'Some name'
    response = post(
        reverse('api:team_credentials_list', kwargs={'version': version, 'pk': team.pk}),
        params,
        org_admin
    )
    assert response.status_code == 201

    response = get(
        reverse('api:team_credentials_list', kwargs={'version': version, 'pk': team.pk}),
        team_member
    )
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_create_team_credential_by_urelated_user_xfail(post, team, organization, alice, team_member, version, params):
    params['team'] = team.id
    params['organization'] = organization.id
    params['name'] = 'Some name'
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        alice
    )
    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_create_team_credential_by_team_member_xfail(post, team, organization, alice, team_member, version, params):
    # Members can't add credentials, only org admins.. for now?
    params['team'] = team.id
    params['organization'] = organization.id
    params['name'] = 'Some name'
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        team_member
    )
    assert response.status_code == 403


#
# Permission granting
#


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_grant_org_credential_to_org_user_through_role_users(post, credential, organization, org_admin, org_member, version):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:role_users_list', kwargs={'version': version, 'pk': credential.use_role.id}), {
        'id': org_member.id
    }, org_admin)
    assert response.status_code == 204


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_grant_org_credential_to_org_user_through_user_roles(post, credential, organization, org_admin, org_member, version):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:user_roles_list', kwargs={'version': version, 'pk': org_member.id}), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 204


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_grant_org_credential_to_non_org_user_through_role_users(post, credential, organization, org_admin, alice, version):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:role_users_list', kwargs={'version': version, 'pk': credential.use_role.id}), {
        'id': alice.id
    }, org_admin)
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_grant_org_credential_to_non_org_user_through_user_roles(post, credential, organization, org_admin, alice, version):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:user_roles_list', kwargs={'version': version, 'pk': alice.id}), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_grant_private_credential_to_user_through_role_users(post, credential, alice, bob, version):
    # normal users can't do this
    credential.admin_role.members.add(alice)
    response = post(reverse('api:role_users_list', kwargs={'version': version, 'pk': credential.use_role.id}), {
        'id': bob.id
    }, alice)
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_grant_private_credential_to_org_user_through_role_users(post, credential, org_admin, org_member, version):
    # org admins can't either
    credential.admin_role.members.add(org_admin)
    response = post(reverse('api:role_users_list', kwargs={'version': version, 'pk': credential.use_role.id}), {
        'id': org_member.id
    }, org_admin)
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_sa_grant_private_credential_to_user_through_role_users(post, credential, admin, bob, version):
    # but system admins can
    response = post(reverse('api:role_users_list', kwargs={'version': version, 'pk': credential.use_role.id}), {
        'id': bob.id
    }, admin)
    assert response.status_code == 204


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_grant_private_credential_to_user_through_user_roles(post, credential, alice, bob, version):
    # normal users can't do this
    credential.admin_role.members.add(alice)
    response = post(reverse('api:user_roles_list', kwargs={'version': version, 'pk': bob.id}), {
        'id': credential.use_role.id
    }, alice)
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_grant_private_credential_to_org_user_through_user_roles(post, credential, org_admin, org_member, version):
    # org admins can't either
    credential.admin_role.members.add(org_admin)
    response = post(reverse('api:user_roles_list', kwargs={'version': version, 'pk': org_member.id}), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_sa_grant_private_credential_to_user_through_user_roles(post, credential, admin, bob, version):
    # but system admins can
    response = post(reverse('api:user_roles_list', kwargs={'version': version, 'pk': bob.id}), {
        'id': credential.use_role.id
    }, admin)
    assert response.status_code == 204


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_grant_org_credential_to_team_through_role_teams(post, credential, organization, org_admin, org_auditor, team, version):
    assert org_auditor not in credential.read_role
    credential.organization = organization
    credential.save()
    response = post(reverse('api:role_teams_list', kwargs={'version': version, 'pk': credential.use_role.id}), {
        'id': team.id
    }, org_admin)
    assert response.status_code == 204
    assert org_auditor in credential.read_role


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_grant_org_credential_to_team_through_team_roles(post, credential, organization, org_admin, org_auditor, team, version):
    assert org_auditor not in credential.read_role
    credential.organization = organization
    credential.save()
    response = post(reverse('api:team_roles_list', kwargs={'version': version, 'pk': team.id}), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 204
    assert org_auditor in credential.read_role


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_sa_grant_private_credential_to_team_through_role_teams(post, credential, admin, team, version):
    # not even a system admin can grant a private cred to a team though
    response = post(reverse('api:role_teams_list', kwargs={'version': version, 'pk': credential.use_role.id}), {
        'id': team.id
    }, admin)
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_sa_grant_private_credential_to_team_through_team_roles(post, credential, admin, team, version):
    # not even a system admin can grant a private cred to a team though
    response = post(reverse('api:role_teams_list', kwargs={'version': version, 'pk': team.id}), {
        'id': credential.use_role.id
    }, admin)
    assert response.status_code == 400


#
# organization credentials
#


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_create_org_credential_as_not_admin(post, organization, org_member, credentialtype_ssh, version, params):
    params['name'] = 'Some name'
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list'),
        params,
        org_member
    )
    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_create_org_credential_as_admin(post, organization, org_admin, credentialtype_ssh, version, params):
    params['name'] = 'Some name'
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        org_admin
    )
    assert response.status_code == 201


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_credential_detail(post, get, organization, org_admin, credentialtype_ssh, version, params):
    params['name'] = 'Some name'
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        org_admin
    )
    assert response.status_code == 201
    response = get(
        reverse('api:credential_detail', kwargs={'version': version, 'pk': response.data['id']}),
        org_admin
    )
    assert response.status_code == 200
    summary_fields = response.data['summary_fields']
    assert 'organization' in summary_fields
    related_fields = response.data['related']
    assert 'organization' in related_fields


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'username': 'someusername'}],
    ['v2', {'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
def test_list_created_org_credentials(post, get, organization, org_admin, org_member, credentialtype_ssh, version, params):
    params['name'] = 'Some name'
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        org_admin
    )
    assert response.status_code == 201

    response = get(
        reverse('api:credential_list', kwargs={'version': version}),
        org_admin
    )
    assert response.status_code == 200
    assert response.data['count'] == 1

    response = get(
        reverse('api:credential_list', kwargs={'version': version}),
        org_member
    )
    assert response.status_code == 200
    assert response.data['count'] == 0

    response = get(
        reverse('api:organization_credential_list', kwargs={'version': version, 'pk': organization.pk}),
        org_admin
    )
    assert response.status_code == 200
    assert response.data['count'] == 1

    response = get(
        reverse('api:organization_credential_list', kwargs={'version': version, 'pk': organization.pk}),
        org_member
    )
    assert response.status_code == 200
    assert response.data['count'] == 0


@pytest.mark.parametrize('order_by', ('password', '-password', 'password,pk', '-password,pk'))
@pytest.mark.parametrize('version', ('v1', 'v2'))
@pytest.mark.django_db
def test_list_cannot_order_by_encrypted_field(post, get, organization, org_admin, credentialtype_ssh, order_by, version):
    for i, password in enumerate(('abc', 'def', 'xyz')):
        response = post(
            reverse('api:credential_list', kwargs={'version': version}),
            {
                'organization': organization.id,
                'name': 'C%d' % i,
                'password': password
            },
            org_admin
        )

    response = get(
        reverse('api:credential_list', kwargs={'version': version}),
        org_admin,
        QUERY_STRING='order_by=%s' % order_by,
        status=400
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_v1_credential_kind_validity(get, post, organization, admin, credentialtype_ssh):
    params = {
        'name': 'Best credential ever',
        'organization': organization.id,
        'kind': 'nonsense'
    }
    response = post(
        reverse('api:credential_list', kwargs={'version': 'v1'}),
        params,
        admin
    )
    assert response.status_code == 400
    assert response.data['kind'] == ['"nonsense" is not a valid choice']


@pytest.mark.django_db
def test_inputs_cannot_contain_extra_fields(get, post, organization, admin, credentialtype_ssh):
    params = {
        'name': 'Best credential ever',
        'organization': organization.id,
        'credential_type': credentialtype_ssh.pk,
        'inputs': {
            'invalid_field': 'foo'
        },
    }
    response = post(
        reverse('api:credential_list', kwargs={'version': 'v2'}),
        params,
        admin
    )
    assert response.status_code == 400
    assert "'invalid_field' was unexpected" in response.data['inputs'][0]


@pytest.mark.django_db
@pytest.mark.parametrize('field_name, field_value', itertools.product(
    ['username', 'password', 'ssh_key_data', 'become_method', 'become_username', 'become_password'],  # noqa
    ['', None]
))
def test_nullish_field_data(get, post, organization, admin, field_name, field_value):
    ssh = CredentialType.defaults['ssh']()
    ssh.save()
    params = {
        'name': 'Best credential ever',
        'credential_type': ssh.pk,
        'organization': organization.id,
        'inputs': {
            field_name: field_value
        }
    }
    response = post(
        reverse('api:credential_list', kwargs={'version': 'v2'}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert getattr(cred, field_name) == ''


@pytest.mark.django_db
@pytest.mark.parametrize('field_value', ['', None, False])
def test_falsey_field_data(get, post, organization, admin, field_value):
    net = CredentialType.defaults['net']()
    net.save()
    params = {
        'name': 'Best credential ever',
        'credential_type': net.pk,
        'organization': organization.id,
        'inputs': {
            'username': 'joe-user',  # username is required
            'authorize': field_value
        }
    }
    response = post(
        reverse('api:credential_list', kwargs={'version': 'v2'}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.authorize is False


@pytest.mark.django_db
@pytest.mark.parametrize('kind, extraneous', [
    ['ssh', 'ssh_key_unlock'],
    ['scm', 'ssh_key_unlock'],
    ['net', 'ssh_key_unlock'],
    ['net', 'authorize_password'],
])
def test_field_dependencies(get, post, organization, admin, kind, extraneous):
    _type = CredentialType.defaults[kind]()
    _type.save()
    params = {
        'name': 'Best credential ever',
        'credential_type': _type.pk,
        'organization': organization.id,
        'inputs': {extraneous: 'not needed'}
    }
    response = post(
        reverse('api:credential_list', kwargs={'version': 'v2'}),
        params,
        admin
    )
    assert response.status_code == 400
    assert re.search('cannot be set unless .+ is set.', smart_str(response.content))

    assert Credential.objects.count() == 0


#
# SCM Credentials
#
@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'scm',
        'name': 'Best credential ever',
        'username': 'some_username',
        'password': 'some_password',
        'ssh_key_data': EXAMPLE_ENCRYPTED_PRIVATE_KEY,
        'ssh_key_unlock': 'some_key_unlock',
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'username': 'some_username',
            'password': 'some_password',
            'ssh_key_data': EXAMPLE_ENCRYPTED_PRIVATE_KEY,
            'ssh_key_unlock': 'some_key_unlock',
        }
    }]
])
def test_scm_create_ok(post, organization, admin, version, params):
    scm = CredentialType.defaults['scm']()
    scm.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['username'] == 'some_username'
    assert decrypt_field(cred, 'password') == 'some_password'
    assert decrypt_field(cred, 'ssh_key_data') == EXAMPLE_ENCRYPTED_PRIVATE_KEY
    assert decrypt_field(cred, 'ssh_key_unlock') == 'some_key_unlock'


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'ssh',
        'name': 'Best credential ever',
        'password': 'secret',
        'vault_password': '',
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'password': 'secret',
        }
    }]
])
def test_ssh_create_ok(post, organization, admin, version, params):
    ssh = CredentialType.defaults['ssh']()
    ssh.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.credential_type == ssh
    assert decrypt_field(cred, 'password') == 'secret'


@pytest.mark.django_db
def test_v1_ssh_vault_ambiguity(post, organization, admin):
    vault = CredentialType.defaults['vault']()
    vault.save()
    params = {
        'organization': organization.id,
        'kind': 'ssh',
        'name': 'Best credential ever',
        'username': 'joe',
        'password': 'secret',
        'ssh_key_data': 'some_key_data',
        'ssh_key_unlock': 'some_key_unlock',
        'vault_password': 'vault_password',
    }
    response = post(
        reverse('api:credential_list', kwargs={'version': 'v1'}),
        params,
        admin
    )
    assert response.status_code == 400


#
# Vault Credentials
#
@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'ssh',
        'name': 'Best credential ever',
        'vault_password': 'some_password',
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'vault_password': 'some_password',
        }
    }]
])
def test_vault_create_ok(post, organization, admin, version, params):
    vault = CredentialType.defaults['vault']()
    vault.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert decrypt_field(cred, 'vault_password') == 'some_password'


@pytest.mark.django_db
def test_vault_password_required(post, organization, admin):
    vault = CredentialType.defaults['vault']()
    vault.save()
    response = post(
        reverse('api:credential_list', kwargs={'version': 'v2'}),
        {
            'credential_type': vault.pk,
            'organization': organization.id,
            'name': 'Best credential ever',
            'inputs': {}
        },
        admin
    )
    assert response.status_code == 400
    assert response.data['inputs'] == {'vault_password': ['required for Vault']}
    assert Credential.objects.count() == 0


#
# Net Credentials
#
@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'net',
        'name': 'Best credential ever',
        'username': 'some_username',
        'password': 'some_password',
        'ssh_key_data': EXAMPLE_ENCRYPTED_PRIVATE_KEY,
        'ssh_key_unlock': 'some_key_unlock',
        'authorize': True,
        'authorize_password': 'some_authorize_password',
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'username': 'some_username',
            'password': 'some_password',
            'ssh_key_data': EXAMPLE_ENCRYPTED_PRIVATE_KEY,
            'ssh_key_unlock': 'some_key_unlock',
            'authorize': True,
            'authorize_password': 'some_authorize_password',
        }
    }]
])
def test_net_create_ok(post, organization, admin, version, params):
    net = CredentialType.defaults['net']()
    net.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['username'] == 'some_username'
    assert decrypt_field(cred, 'password') == 'some_password'
    assert decrypt_field(cred, 'ssh_key_data') == EXAMPLE_ENCRYPTED_PRIVATE_KEY
    assert decrypt_field(cred, 'ssh_key_unlock') == 'some_key_unlock'
    assert decrypt_field(cred, 'authorize_password') == 'some_authorize_password'
    assert cred.inputs['authorize'] is True


#
# Cloudforms Credentials
#
@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'cloudforms',
        'name': 'Best credential ever',
        'host': 'some_host',
        'username': 'some_username',
        'password': 'some_password',
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'host': 'some_host',
            'username': 'some_username',
            'password': 'some_password',
        }
    }]
])
def test_cloudforms_create_ok(post, organization, admin, version, params):
    cloudforms = CredentialType.defaults['cloudforms']()
    cloudforms.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['host'] == 'some_host'
    assert cred.inputs['username'] == 'some_username'
    assert decrypt_field(cred, 'password') == 'some_password'


#
# GCE Credentials
#
@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'gce',
        'name': 'Best credential ever',
        'username': 'some_username',
        'project': 'some_project',
        'ssh_key_data': EXAMPLE_PRIVATE_KEY,
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'username': 'some_username',
            'project': 'some_project',
            'ssh_key_data': EXAMPLE_PRIVATE_KEY,
        }
    }]
])
def test_gce_create_ok(post, organization, admin, version, params):
    gce = CredentialType.defaults['gce']()
    gce.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['username'] == 'some_username'
    assert cred.inputs['project'] == 'some_project'
    assert decrypt_field(cred, 'ssh_key_data') == EXAMPLE_PRIVATE_KEY


#
# Azure Resource Manager
#
@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'azure_rm',
        'name': 'Best credential ever',
        'subscription': 'some_subscription',
        'username': 'some_username',
        'password': 'some_password',
        'client': 'some_client',
        'secret': 'some_secret',
        'tenant': 'some_tenant'
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'subscription': 'some_subscription',
            'username': 'some_username',
            'password': 'some_password',
            'client': 'some_client',
            'secret': 'some_secret',
            'tenant': 'some_tenant'
        }
    }]
])
def test_azure_rm_create_ok(post, organization, admin, version, params):
    azure_rm = CredentialType.defaults['azure_rm']()
    azure_rm.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['subscription'] == 'some_subscription'
    assert cred.inputs['username'] == 'some_username'
    assert decrypt_field(cred, 'password') == 'some_password'
    assert cred.inputs['client'] == 'some_client'
    assert decrypt_field(cred, 'secret') == 'some_secret'
    assert cred.inputs['tenant'] == 'some_tenant'


#
# RH Satellite6 Credentials
#
@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'satellite6',
        'name': 'Best credential ever',
        'host': 'some_host',
        'username': 'some_username',
        'password': 'some_password',
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'host': 'some_host',
            'username': 'some_username',
            'password': 'some_password',
        }
    }]
])
def test_satellite6_create_ok(post, organization, admin, version, params):
    sat6 = CredentialType.defaults['satellite6']()
    sat6.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['host'] == 'some_host'
    assert cred.inputs['username'] == 'some_username'
    assert decrypt_field(cred, 'password') == 'some_password'


#
# AWS Credentials
#
@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'aws',
        'name': 'Best credential ever',
        'username': 'some_username',
        'password': 'some_password',
        'security_token': 'abc123'
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'username': 'some_username',
            'password': 'some_password',
            'security_token': 'abc123'
        }
    }]
])
def test_aws_create_ok(post, organization, admin, version, params):
    aws = CredentialType.defaults['aws']()
    aws.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['username'] == 'some_username'
    assert decrypt_field(cred, 'password') == 'some_password'
    assert decrypt_field(cred, 'security_token') == 'abc123'


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'aws',
        'name': 'Best credential ever',
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {}
    }]
])
def test_aws_create_fail_required_fields(post, organization, admin, version, params):
    aws = CredentialType.defaults['aws']()
    aws.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 400

    assert Credential.objects.count() == 0
    errors = response.data
    if version == 'v2':
        errors = response.data['inputs']
    assert errors['username'] == ['required for %s' % aws.name]
    assert errors['password'] == ['required for %s' % aws.name]


#
# VMware vCenter Credentials
#
@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'vmware',
        'host': 'some_host',
        'name': 'Best credential ever',
        'username': 'some_username',
        'password': 'some_password'
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'host': 'some_host',
            'username': 'some_username',
            'password': 'some_password'
        }
    }]
])
def test_vmware_create_ok(post, organization, admin, version, params):
    vmware = CredentialType.defaults['vmware']()
    vmware.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['host'] == 'some_host'
    assert cred.inputs['username'] == 'some_username'
    assert decrypt_field(cred, 'password') == 'some_password'


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'vmware',
        'name': 'Best credential ever',
    }],
    ['v2', {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {}
    }]
])
def test_vmware_create_fail_required_fields(post, organization, admin, version, params):
    vmware = CredentialType.defaults['vmware']()
    vmware.save()
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 400

    assert Credential.objects.count() == 0
    errors = response.data
    if version == 'v2':
        errors = response.data['inputs']
    assert errors['username'] == ['required for %s' % vmware.name]
    assert errors['password'] == ['required for %s' % vmware.name]
    assert errors['host'] == ['required for %s' % vmware.name]


#
# Openstack Credentials
#
@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'username': 'some_user',
        'password': 'some_password',
        'project': 'some_project',
        'host': 'some_host',
    }],
    ['v2', {
        'credential_type': 1,
        'inputs': {
            'username': 'some_user',
            'password': 'some_password',
            'project': 'some_project',
            'host': 'some_host',
        }
    }]
])
def test_openstack_create_ok(post, organization, admin, version, params):
    openstack = CredentialType.defaults['openstack']()
    openstack.save()
    params['kind'] = 'openstack'
    params['name'] = 'Best credential ever'
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201


@pytest.mark.django_db
@pytest.mark.parametrize('verify_ssl, expected', [
    [None, True],
    [True, True],
    [False, False],
])
def test_openstack_verify_ssl(get, post, organization, admin, verify_ssl, expected):
    openstack = CredentialType.defaults['openstack']()
    openstack.save()
    inputs = {
        'username': 'some_user',
        'password': 'some_password',
        'project': 'some_project',
        'host': 'some_host',
    }
    if verify_ssl is not None:
        inputs['verify_ssl'] = verify_ssl
    params = {
        'credential_type': openstack.id,
        'inputs': inputs,
        'name': 'Best credential ever',
        'organization': organization.id
    }
    response = post(
        reverse('api:credential_list', kwargs={'version': 'v2'}),
        params,
        admin
    )
    assert response.status_code == 201

    cred = Credential.objects.get(pk=response.data['id'])
    assert cred.get_input('verify_ssl') == expected


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {}],
    ['v2', {
        'credential_type': 1,
        'inputs': {}
    }]
])
def test_openstack_create_fail_required_fields(post, organization, admin, version, params):
    openstack = CredentialType.defaults['openstack']()
    openstack.save()
    params['kind'] = 'openstack'
    params['name'] = 'Best credential ever'
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 400
    errors = response.data
    if version == 'v2':
        errors = response.data['inputs']
    assert errors['username'] == ['required for %s' % openstack.name]
    assert errors['password'] == ['required for %s' % openstack.name]
    assert errors['host'] == ['required for %s' % openstack.name]
    assert errors['project'] == ['required for %s' % openstack.name]


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'name': 'Best credential ever',
        'kind': 'ssh',
        'username': 'joe',
        'password': '',
    }],
    ['v2', {
        'name': 'Best credential ever',
        'credential_type': 1,
        'inputs': {
            'username': 'joe',
            'password': '',
        }
    }]
])
def test_field_removal(put, organization, admin, credentialtype_ssh, version, params):
    cred = Credential(
        credential_type=credentialtype_ssh,
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'jim',
            'password': u'secret'
        }
    )
    cred.save()

    params['organization'] = organization.id
    response = put(
        reverse('api:credential_detail', kwargs={'version': version, 'pk': cred.pk}),
        params,
        admin
    )
    assert response.status_code == 200

    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['username'] == 'joe'
    assert 'password' not in cred.inputs


@pytest.mark.django_db
@pytest.mark.parametrize('relation, related_obj', [
    ['ad_hoc_commands', AdHocCommand()],
    ['insights_inventories', Inventory()],
    ['unifiedjobs', Job()],
    ['unifiedjobtemplates', JobTemplate()],
    ['unifiedjobtemplates', InventorySource()],
    ['projects', Project()],
    ['workflowjobnodes', WorkflowJobNode()],
])
def test_credential_type_mutability(patch, organization, admin, credentialtype_ssh,
                                    credentialtype_aws, relation, related_obj):
    cred = Credential(
        credential_type=credentialtype_ssh,
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'jim',
            'password': u'pass'
        }
    )
    cred.save()

    related_obj.save()
    getattr(cred, relation).add(related_obj)

    def _change_credential_type():
        return patch(
            reverse('api:credential_detail', kwargs={'version': 'v2', 'pk': cred.pk}),
            {
                'credential_type': credentialtype_aws.pk,
                'inputs': {
                    'username': u'jim',
                    'password': u'pass'
                }
            },
            admin
        )

    response = _change_credential_type()
    assert response.status_code == 400
    expected = ['You cannot change the credential type of the credential, '
                'as it may break the functionality of the resources using it.']
    assert response.data['credential_type'] == expected

    response = patch(
        reverse('api:credential_detail', kwargs={'version': 'v2', 'pk': cred.pk}),
        {'name': 'Worst credential ever'},
        admin
    )
    assert response.status_code == 200
    assert Credential.objects.get(pk=cred.pk).name == 'Worst credential ever'

    related_obj.delete()
    response = _change_credential_type()
    assert response.status_code == 200


@pytest.mark.django_db
def test_vault_credential_type_mutability(patch, organization, admin, credentialtype_ssh,
                                          credentialtype_vault):
    cred = Credential(
        credential_type=credentialtype_vault,
        name='Best credential ever',
        organization=organization,
        inputs={
            'vault_password': u'some-vault',
        }
    )
    cred.save()

    jt = JobTemplate()
    jt.save()
    jt.credentials.add(cred)

    def _change_credential_type():
        return patch(
            reverse('api:credential_detail', kwargs={'version': 'v2', 'pk': cred.pk}),
            {
                'credential_type': credentialtype_ssh.pk,
                'inputs': {
                    'username': u'jim',
                    'password': u'pass'
                }
            },
            admin
        )

    response = _change_credential_type()
    assert response.status_code == 400
    expected = ['You cannot change the credential type of the credential, '
                'as it may break the functionality of the resources using it.']
    assert response.data['credential_type'] == expected

    response = patch(
        reverse('api:credential_detail', kwargs={'version': 'v2', 'pk': cred.pk}),
        {'name': 'Worst credential ever'},
        admin
    )
    assert response.status_code == 200
    assert Credential.objects.get(pk=cred.pk).name == 'Worst credential ever'

    jt.delete()
    response = _change_credential_type()
    assert response.status_code == 200


@pytest.mark.django_db
def test_cloud_credential_type_mutability(patch, organization, admin, credentialtype_ssh,
                                          credentialtype_aws):
    cred = Credential(
        credential_type=credentialtype_aws,
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'jim',
            'password': u'pass'
        }
    )
    cred.save()

    jt = JobTemplate()
    jt.save()
    jt.credentials.add(cred)

    def _change_credential_type():
        return patch(
            reverse('api:credential_detail', kwargs={'version': 'v2', 'pk': cred.pk}),
            {
                'credential_type': credentialtype_ssh.pk,
                'inputs': {
                    'username': u'jim',
                    'password': u'pass'
                }
            },
            admin
        )

    response = _change_credential_type()
    assert response.status_code == 400
    expected = ['You cannot change the credential type of the credential, '
                'as it may break the functionality of the resources using it.']
    assert response.data['credential_type'] == expected

    response = patch(
        reverse('api:credential_detail', kwargs={'version': 'v2', 'pk': cred.pk}),
        {'name': 'Worst credential ever'},
        admin
    )
    assert response.status_code == 200
    assert Credential.objects.get(pk=cred.pk).name == 'Worst credential ever'

    jt.delete()
    response = _change_credential_type()
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'name': 'Best credential ever',
        'kind': 'ssh',
        'username': 'joe',
        'ssh_key_data': '$encrypted$',
    }],
    ['v2', {
        'name': 'Best credential ever',
        'credential_type': 1,
        'inputs': {
            'username': 'joe',
            'ssh_key_data': '$encrypted$',
        }
    }]
])
def test_ssh_unlock_needed(put, organization, admin, credentialtype_ssh, version, params):
    cred = Credential(
        credential_type=credentialtype_ssh,
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'joe',
            'ssh_key_data': EXAMPLE_ENCRYPTED_PRIVATE_KEY,
            'ssh_key_unlock': 'unlock'
        }
    )
    cred.save()

    params['organization'] = organization.id
    response = put(
        reverse('api:credential_detail', kwargs={'version': version, 'pk': cred.pk}),
        params,
        admin
    )
    assert response.status_code == 400
    assert response.data['inputs']['ssh_key_unlock'] == ['must be set when SSH key is encrypted.']


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'name': 'Best credential ever',
        'kind': 'ssh',
        'username': 'joe',
        'ssh_key_data': '$encrypted$',
        'ssh_key_unlock': 'superfluous-key-unlock',
    }],
    ['v2', {
        'name': 'Best credential ever',
        'credential_type': 1,
        'inputs': {
            'username': 'joe',
            'ssh_key_data': '$encrypted$',
            'ssh_key_unlock': 'superfluous-key-unlock',
        }
    }]
])
def test_ssh_unlock_not_needed(put, organization, admin, credentialtype_ssh, version, params):
    cred = Credential(
        credential_type=credentialtype_ssh,
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'joe',
            'ssh_key_data': EXAMPLE_PRIVATE_KEY,
        }
    )
    cred.save()

    params['organization'] = organization.id
    response = put(
        reverse('api:credential_detail', kwargs={'version': version, 'pk': cred.pk}),
        params,
        admin
    )
    assert response.status_code == 400
    assert response.data['inputs']['ssh_key_unlock'] == ['should not be set when SSH key is not encrypted.']


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'name': 'Best credential ever',
        'kind': 'ssh',
        'username': 'joe',
        'ssh_key_data': '$encrypted$',
        'ssh_key_unlock': 'new-unlock',
    }],
    ['v2', {
        'name': 'Best credential ever',
        'credential_type': 1,
        'inputs': {
            'username': 'joe',
            'ssh_key_data': '$encrypted$',
            'ssh_key_unlock': 'new-unlock',
        }
    }]
])
def test_ssh_unlock_with_prior_value(put, organization, admin, credentialtype_ssh, version, params):
    cred = Credential(
        credential_type=credentialtype_ssh,
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'joe',
            'ssh_key_data': EXAMPLE_ENCRYPTED_PRIVATE_KEY,
            'ssh_key_unlock': 'old-unlock'
        }
    )
    cred.save()

    params['organization'] = organization.id
    response = put(
        reverse('api:credential_detail', kwargs={'version': version, 'pk': cred.pk}),
        params,
        admin
    )
    assert response.status_code == 200

    cred = Credential.objects.all()[:1].get()
    assert decrypt_field(cred, 'ssh_key_unlock') == 'new-unlock'


#
# test secret encryption/decryption
#

@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'kind': 'ssh',
        'username': 'joe',
        'password': 'secret',
    }],
    ['v2', {
        'credential_type': 1,
        'inputs': {
            'username': 'joe',
            'password': 'secret',
        }
    }]
])
def test_secret_encryption_on_create(get, post, organization, admin, credentialtype_ssh, version, params):
    params['name'] = 'Best credential ever'
    params['organization'] = organization.id
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 201

    response = get(
        reverse('api:credential_list', kwargs={'version': version}),
        admin
    )
    assert response.status_code == 200
    assert response.data['count'] == 1
    cred = response.data['results'][0]
    if version == 'v1':
        assert cred['username'] == 'joe'
        assert cred['password'] == '$encrypted$'
    elif version == 'v2':
        assert cred['inputs']['username'] == 'joe'
        assert cred['inputs']['password'] == '$encrypted$'

    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['password'].startswith('$encrypted$UTF8$AES')
    assert decrypt_field(cred, 'password') == 'secret'


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {'password': 'secret'}],
    ['v2', {'inputs': {'username': 'joe', 'password': 'secret'}}]
])
def test_secret_encryption_on_update(get, post, patch, organization, admin, credentialtype_ssh, version, params):
    response = post(
        reverse('api:credential_list', kwargs={'version': 'v2'}),
        {
            'name': 'Best credential ever',
            'organization': organization.id,
            'credential_type': 1,
            'inputs': {
                'username': 'joe',
            }
        },
        admin
    )
    assert response.status_code == 201

    response = patch(
        reverse('api:credential_detail', kwargs={'pk': 1, 'version': version}),
        params,
        admin
    )
    assert response.status_code == 200

    response = get(
        reverse('api:credential_list', kwargs={'version': version}),
        admin
    )
    assert response.status_code == 200
    assert response.data['count'] == 1
    cred = response.data['results'][0]
    if version == 'v1':
        assert cred['username'] == 'joe'
        assert cred['password'] == '$encrypted$'
    elif version == 'v2':
        assert cred['inputs']['username'] == 'joe'
        assert cred['inputs']['password'] == '$encrypted$'

    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['password'].startswith('$encrypted$UTF8$AES')
    assert decrypt_field(cred, 'password') == 'secret'


@pytest.mark.django_db
@pytest.mark.parametrize('version, params', [
    ['v1', {
        'username': 'joe',
        'password': '$encrypted$',
    }],
    ['v2', {
        'inputs': {
            'username': 'joe',
            'password': '$encrypted$',
        }
    }]
])
def test_secret_encryption_previous_value(patch, organization, admin, credentialtype_ssh, version, params):
    cred = Credential(
        credential_type=credentialtype_ssh,
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'jim',
            'password': u'secret'
        }
    )
    cred.save()

    assert decrypt_field(cred, 'password') == 'secret'
    response = patch(
        reverse('api:credential_detail', kwargs={'pk': cred.pk, 'version': version}),
        params,
        admin
    )
    assert response.status_code == 200

    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['username'] == 'joe'
    assert cred.inputs['password'].startswith('$encrypted$UTF8$AES')
    assert decrypt_field(cred, 'password') == 'secret'


@pytest.mark.django_db
def test_custom_credential_type_create(get, post, organization, admin):
    credential_type = CredentialType(
        kind='cloud',
        name='MyCloud',
        inputs = {
            'fields': [{
                'id': 'api_token',
                'label': 'API Token',
                'type': 'string',
                'secret': True
            }]
        }
    )
    credential_type.save()
    params = {
        'name': 'Best credential ever',
        'organization': organization.pk,
        'credential_type': credential_type.pk,
        'inputs': {
            'api_token': 'secret'
        }
    }
    response = post(
        reverse('api:credential_list', kwargs={'version': 'v2'}),
        params,
        admin
    )
    assert response.status_code == 201

    response = get(
        reverse('api:credential_list', kwargs={'version': 'v2'}),
        admin
    )
    assert response.status_code == 200
    assert response.data['count'] == 1
    cred = response.data['results'][0]
    assert cred['inputs']['api_token'] == '$encrypted$'

    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['api_token'].startswith('$encrypted$UTF8$AES')
    assert decrypt_field(cred, 'api_token') == 'secret'


#
# misc xfail conditions
#


@pytest.mark.parametrize('version, params', [
    ['v1', {'name': 'Some name', 'username': 'someusername'}],
    ['v2', {'name': 'Some name', 'credential_type': 1, 'inputs': {'username': 'someusername'}}]
])
@pytest.mark.django_db
def test_create_credential_missing_user_team_org_xfail(post, admin, credentialtype_ssh, version, params):
    # Must specify one of user, team, or organization
    response = post(
        reverse('api:credential_list', kwargs={'version': version}),
        params,
        admin
    )
    assert response.status_code == 400
