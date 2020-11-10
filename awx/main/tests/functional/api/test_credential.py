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


#
# user credential creation
#


@pytest.mark.django_db
def test_create_user_credential_via_credentials_list(post, get, alice, credentialtype_ssh):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'user': alice.id,
        'name': 'Some name',
    }
    response = post(reverse('api:credential_list'), params, alice)
    assert response.status_code == 201

    response = get(reverse('api:credential_list'), alice)
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_credential_validation_error_with_bad_user(post, admin, credentialtype_ssh):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'user': 'asdf',
        'name': 'Some name'
    }
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 400
    assert response.data['user'][0] == 'Incorrect type. Expected pk value, received str.'


@pytest.mark.django_db
def test_credential_validation_error_with_no_owner_field(post, admin, credentialtype_ssh):
    params = {
        'credential_type': credentialtype_ssh.id,
        'inputs': {'username': 'someusername'},
        'name': 'Some name',
    }
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 400
    assert response.data['detail'][0] == "Missing 'user', 'team', or 'organization'."


@pytest.mark.django_db
def test_credential_validation_error_with_multiple_owner_fields(post, admin, alice, team, organization, credentialtype_ssh):
    params = {
        'credential_type': credentialtype_ssh.id,
        'inputs': {'username': 'someusername'},
        'team': team.id,
        'user': alice.id,
        'organization': organization.id,
        'name': 'Some name',
    }
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 400
    assert response.data['detail'][0] == (
        "Only one of 'user', 'team', or 'organization' should be provided, "
        "received organization, team, user fields."
    )


@pytest.mark.django_db
def test_create_user_credential_via_user_credentials_list(post, get, alice, credentialtype_ssh):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'user': alice.id,
        'name': 'Some name',
    }
    response = post(
        reverse('api:user_credentials_list', kwargs={'pk': alice.pk}),
        params,
        alice
    )
    assert response.status_code == 201

    response = get(reverse('api:user_credentials_list', kwargs={'pk': alice.pk}), alice)
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_create_user_credential_via_credentials_list_xfail(post, alice, bob):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'user': bob.id,
        'name': 'Some name',
    }
    params['user'] = bob.id
    params['name'] = 'Some name'
    response = post(reverse('api:credential_list'), params, alice)
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_user_credential_via_user_credentials_list_xfail(post, alice, bob):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'user': bob.id,
        'name': 'Some name',
    }
    response = post(
        reverse('api:user_credentials_list', kwargs={'pk': bob.pk}),
        params,
        alice
    )
    assert response.status_code == 403


#
# team credential creation
#


@pytest.mark.django_db
def test_create_team_credential(post, get, team, organization, org_admin, team_member, credentialtype_ssh):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'team': team.id,
        'name': 'Some name',
    }
    response = post(reverse('api:credential_list'), params, org_admin)
    assert response.status_code == 201

    response = get(
        reverse('api:team_credentials_list', kwargs={'pk': team.pk}),
        team_member
    )
    assert response.status_code == 200
    assert response.data['count'] == 1

    # Assure that credential's organization is implictly set to team's org
    assert response.data['results'][0]['summary_fields']['organization']['id'] == team.organization.id


@pytest.mark.django_db
def test_create_team_credential_via_team_credentials_list(post, get, team, org_admin, team_member, credentialtype_ssh):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'team': team.id,
        'name': 'Some name',
    }
    response = post(
        reverse('api:team_credentials_list', kwargs={'pk': team.pk}),
        params,
        org_admin
    )
    assert response.status_code == 201

    response = get(
        reverse('api:team_credentials_list', kwargs={'pk': team.pk}),
        team_member
    )
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_create_team_credential_by_urelated_user_xfail(post, team, organization, alice, team_member):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'team': team.id,
        'organization': organization.id,
        'name': 'Some name',
    }
    response = post(reverse('api:credential_list'), params, alice)
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_team_credential_by_team_member_xfail(post, team, organization, alice, team_member):
    # Members can't add credentials, only org admins.. for now?
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'team': team.id,
        'organization': organization.id,
        'name': 'Some name',
    }
    response = post(reverse('api:credential_list'), params, team_member)
    assert response.status_code == 403


#
# Permission granting
#


@pytest.mark.django_db
def test_grant_org_credential_to_org_user_through_role_users(post, credential, organization, org_admin, org_member):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:role_users_list', kwargs={'pk': credential.use_role.id}), {
        'id': org_member.id
    }, org_admin)
    assert response.status_code == 204


@pytest.mark.django_db
def test_grant_org_credential_to_org_user_through_user_roles(post, credential, organization, org_admin, org_member):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:user_roles_list', kwargs={'pk': org_member.id}), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 204


@pytest.mark.django_db
def test_grant_org_credential_to_non_org_user_through_role_users(post, credential, organization, org_admin, alice):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:role_users_list', kwargs={'pk': credential.use_role.id}), {
        'id': alice.id
    }, org_admin)
    assert response.status_code == 400


@pytest.mark.django_db
def test_grant_org_credential_to_non_org_user_through_user_roles(post, credential, organization, org_admin, alice):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:user_roles_list', kwargs={'pk': alice.id}), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 400


@pytest.mark.django_db
def test_grant_private_credential_to_user_through_role_users(post, credential, alice, bob):
    # normal users can't do this
    credential.admin_role.members.add(alice)
    response = post(reverse('api:role_users_list', kwargs={'pk': credential.use_role.id}), {
        'id': bob.id
    }, alice)
    assert response.status_code == 400


@pytest.mark.django_db
def test_grant_private_credential_to_org_user_through_role_users(post, credential, org_admin, org_member):
    # org admins can't either
    credential.admin_role.members.add(org_admin)
    response = post(reverse('api:role_users_list', kwargs={'pk': credential.use_role.id}), {
        'id': org_member.id
    }, org_admin)
    assert response.status_code == 400


@pytest.mark.django_db
def test_sa_grant_private_credential_to_user_through_role_users(post, credential, admin, bob):
    # but system admins can
    response = post(reverse('api:role_users_list', kwargs={'pk': credential.use_role.id}), {
        'id': bob.id
    }, admin)
    assert response.status_code == 204


@pytest.mark.django_db
def test_grant_private_credential_to_user_through_user_roles(post, credential, alice, bob):
    # normal users can't do this
    credential.admin_role.members.add(alice)
    response = post(reverse('api:user_roles_list', kwargs={'pk': bob.id}), {
        'id': credential.use_role.id
    }, alice)
    assert response.status_code == 400


@pytest.mark.django_db
def test_grant_private_credential_to_org_user_through_user_roles(post, credential, org_admin, org_member):
    # org admins can't either
    credential.admin_role.members.add(org_admin)
    response = post(reverse('api:user_roles_list', kwargs={'pk': org_member.id}), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 400


@pytest.mark.django_db
def test_sa_grant_private_credential_to_user_through_user_roles(post, credential, admin, bob):
    # but system admins can
    response = post(reverse('api:user_roles_list', kwargs={'pk': bob.id}), {
        'id': credential.use_role.id
    }, admin)
    assert response.status_code == 204


@pytest.mark.django_db
def test_grant_org_credential_to_team_through_role_teams(post, credential, organization, org_admin, org_auditor, team):
    assert org_auditor not in credential.read_role
    credential.organization = organization
    credential.save()
    response = post(reverse('api:role_teams_list', kwargs={'pk': credential.use_role.id}), {
        'id': team.id
    }, org_admin)
    assert response.status_code == 204
    assert org_auditor in credential.read_role


@pytest.mark.django_db
def test_grant_org_credential_to_team_through_team_roles(post, credential, organization, org_admin, org_auditor, team):
    assert org_auditor not in credential.read_role
    credential.organization = organization
    credential.save()
    response = post(reverse('api:team_roles_list', kwargs={'pk': team.id}), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 204
    assert org_auditor in credential.read_role


@pytest.mark.django_db
def test_sa_grant_private_credential_to_team_through_role_teams(post, credential, admin, team):
    # not even a system admin can grant a private cred to a team though
    response = post(reverse('api:role_teams_list', kwargs={'pk': credential.use_role.id}), {
        'id': team.id
    }, admin)
    assert response.status_code == 400


@pytest.mark.django_db
def test_sa_grant_private_credential_to_team_through_team_roles(post, credential, admin, team):
    # not even a system admin can grant a private cred to a team though
    response = post(reverse('api:role_teams_list', kwargs={'pk': team.id}), {
        'id': credential.use_role.id
    }, admin)
    assert response.status_code == 400


#
# organization credentials
#


@pytest.mark.django_db
def test_create_org_credential_as_not_admin(post, organization, org_member, credentialtype_ssh):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'name': 'Some name',
        'organization': organization.id,
    }
    response = post(
        reverse('api:credential_list'),
        params,
        org_member
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_create_org_credential_as_admin(post, organization, org_admin, credentialtype_ssh):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'name': 'Some name',
        'organization': organization.id,
    }
    response = post(reverse('api:credential_list'), params, org_admin)
    assert response.status_code == 201


@pytest.mark.django_db
def test_credential_detail(post, get, organization, org_admin, credentialtype_ssh):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'name': 'Some name',
        'organization': organization.id,
    }
    response = post(
        reverse('api:credential_list'),
        params,
        org_admin
    )
    assert response.status_code == 201
    response = get(
        reverse('api:credential_detail', kwargs={'pk': response.data['id']}),
        org_admin
    )
    assert response.status_code == 200
    summary_fields = response.data['summary_fields']
    assert 'organization' in summary_fields
    related_fields = response.data['related']
    assert 'organization' in related_fields


@pytest.mark.django_db
def test_list_created_org_credentials(post, get, organization, org_admin, org_member, credentialtype_ssh):
    params = {
        'credential_type': 1,
        'inputs': {'username': 'someusername'},
        'name': 'Some name',
        'organization': organization.id,
    }
    response = post(
        reverse('api:credential_list'),
        params,
        org_admin
    )
    assert response.status_code == 201

    response = get(
        reverse('api:credential_list'),
        org_admin
    )
    assert response.status_code == 200
    assert response.data['count'] == 1

    response = get(
        reverse('api:credential_list'),
        org_member
    )
    assert response.status_code == 200
    assert response.data['count'] == 0

    response = get(
        reverse('api:organization_credential_list', kwargs={'pk': organization.pk}),
        org_admin
    )
    assert response.status_code == 200
    assert response.data['count'] == 1

    response = get(
        reverse('api:organization_credential_list', kwargs={'pk': organization.pk}),
        org_member
    )
    assert response.status_code == 200
    assert response.data['count'] == 0


@pytest.mark.parametrize('order_by', ('password', '-password', 'password,pk', '-password,pk'))
@pytest.mark.django_db
def test_list_cannot_order_by_encrypted_field(post, get, organization, org_admin, credentialtype_ssh, order_by):
    for i, password in enumerate(('abc', 'def', 'xyz')):
        response = post(
            reverse('api:credential_list'),
            {
                'organization': organization.id,
                'name': 'C%d' % i,
                'password': password
            },
            org_admin
        )

    response = get(
        reverse('api:credential_list'),
        org_admin,
        QUERY_STRING='order_by=%s' % order_by,
        status=400
    )
    assert response.status_code == 400


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
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 400
    assert "'invalid_field' was unexpected" in response.data['inputs'][0]


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
            'username': 'joe-user',
            'authorize': field_value
        }
    }
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['authorize'] is False


@pytest.mark.django_db
@pytest.mark.parametrize('kind, extraneous', [
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
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 400
    assert re.search('cannot be set unless .+ is set.', smart_str(response.content))

    assert Credential.objects.count() == 0


#
# SCM Credentials
#
@pytest.mark.django_db
def test_scm_create_ok(post, organization, admin):
    params = {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'username': 'some_username',
            'password': 'some_password',
            'ssh_key_data': EXAMPLE_ENCRYPTED_PRIVATE_KEY,
            'ssh_key_unlock': 'some_key_unlock',
        }
    }
    scm = CredentialType.defaults['scm']()
    scm.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['username'] == 'some_username'
    assert decrypt_field(cred, 'password') == 'some_password'
    assert decrypt_field(cred, 'ssh_key_data') == EXAMPLE_ENCRYPTED_PRIVATE_KEY
    assert decrypt_field(cred, 'ssh_key_unlock') == 'some_key_unlock'


@pytest.mark.django_db
def test_ssh_create_ok(post, organization, admin):
    params = {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'password': 'secret',
        }
    }
    ssh = CredentialType.defaults['ssh']()
    ssh.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.credential_type == ssh
    assert decrypt_field(cred, 'password') == 'secret'


#
# Vault Credentials
#
@pytest.mark.django_db
def test_vault_create_ok(post, organization, admin):
    params = {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'vault_password': 'some_password',
        }
    }
    vault = CredentialType.defaults['vault']()
    vault.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert decrypt_field(cred, 'vault_password') == 'some_password'


@pytest.mark.django_db
def test_vault_password_required(post, organization, admin):
    vault = CredentialType.defaults['vault']()
    vault.save()
    response = post(
        reverse('api:credential_list'),
        {
            'credential_type': vault.pk,
            'organization': organization.id,
            'name': 'Best credential ever',
            'inputs': {}
        },
        admin
    )
    assert response.status_code == 201
    assert Credential.objects.count() == 1

    # vault_password must be specified by launch time
    j = Job()
    j.save()
    j.credentials.add(Credential.objects.first())
    assert j.pre_start() == (False, None)
    assert 'required fields (vault_password)' in j.job_explanation


#
# Net Credentials
#
@pytest.mark.django_db
def test_net_create_ok(post, organization, admin):
    params = {
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
    }
    net = CredentialType.defaults['net']()
    net.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
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
# GCE Credentials
#
@pytest.mark.django_db
def test_gce_create_ok(post, organization, admin):
    params = {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'username': 'some_username',
            'project': 'some_project',
            'ssh_key_data': EXAMPLE_PRIVATE_KEY,
        }
    }
    gce = CredentialType.defaults['gce']()
    gce.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
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
def test_azure_rm_create_ok(post, organization, admin):
    params = {
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
    }
    azure_rm = CredentialType.defaults['azure_rm']()
    azure_rm.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
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
def test_satellite6_create_ok(post, organization, admin):
    params = {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'host': 'some_host',
            'username': 'some_username',
            'password': 'some_password',
        }
    }
    sat6 = CredentialType.defaults['satellite6']()
    sat6.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
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
def test_aws_create_ok(post, organization, admin):
    params = {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'username': 'some_username',
            'password': 'some_password',
            'security_token': 'abc123'
        }
    }
    aws = CredentialType.defaults['aws']()
    aws.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['username'] == 'some_username'
    assert decrypt_field(cred, 'password') == 'some_password'
    assert decrypt_field(cred, 'security_token') == 'abc123'


@pytest.mark.django_db
def test_aws_create_fail_required_fields(post, organization, admin):
    params = {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {}
    }
    aws = CredentialType.defaults['aws']()
    aws.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201
    assert Credential.objects.count() == 1

    # username and password must be specified by launch time
    j = Job()
    j.save()
    j.credentials.add(Credential.objects.first())
    assert j.pre_start() == (False, None)
    assert 'required fields (password, username)' in j.job_explanation


#
# VMware vCenter Credentials
#
@pytest.mark.django_db
def test_vmware_create_ok(post, organization, admin):
    params = {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {
            'host': 'some_host',
            'username': 'some_username',
            'password': 'some_password'
        }
    }
    vmware = CredentialType.defaults['vmware']()
    vmware.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201

    assert Credential.objects.count() == 1
    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['host'] == 'some_host'
    assert cred.inputs['username'] == 'some_username'
    assert decrypt_field(cred, 'password') == 'some_password'


@pytest.mark.django_db
def test_vmware_create_fail_required_fields(post, organization, admin):
    params = {
        'credential_type': 1,
        'name': 'Best credential ever',
        'inputs': {}
    }
    vmware = CredentialType.defaults['vmware']()
    vmware.save()
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201
    assert Credential.objects.count() == 1

    # username, password, and host must be specified by launch time
    j = Job()
    j.save()
    j.credentials.add(Credential.objects.first())
    assert j.pre_start() == (False, None)
    assert 'required fields (host, password, username)' in j.job_explanation


#
# Openstack Credentials
#
@pytest.mark.django_db
def test_openstack_create_ok(post, organization, admin):
    params = {
        'credential_type': 1,
        'inputs': {
            'username': 'some_user',
            'password': 'some_password',
            'project': 'some_project',
            'host': 'some_host',
        }
    }
    openstack = CredentialType.defaults['openstack']()
    openstack.save()
    params['kind'] = 'openstack'
    params['name'] = 'Best credential ever'
    params['organization'] = organization.id
    response = post(reverse('api:credential_list'), params, admin)
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
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201

    cred = Credential.objects.get(pk=response.data['id'])
    assert cred.get_input('verify_ssl') == expected


@pytest.mark.django_db
def test_openstack_create_fail_required_fields(post, organization, admin):
    openstack = CredentialType.defaults['openstack']()
    openstack.save()
    params = {
        'credential_type': 1,
        'inputs': {},
        'kind': 'openstack',
        'name': 'Best credential ever',
        'organization': organization.id,
    }
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201

    # username, password, host, and project must be specified by launch time
    j = Job()
    j.save()
    j.credentials.add(Credential.objects.first())
    assert j.pre_start() == (False, None)
    assert 'required fields (host, password, project, username)' in j.job_explanation


@pytest.mark.django_db
def test_field_removal(put, organization, admin, credentialtype_ssh):
    params = {
        'name': 'Best credential ever',
        'credential_type': 1,
        'inputs': {
            'username': 'joe',
            'password': '',
        }
    }
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
        reverse('api:credential_detail', kwargs={'pk': cred.pk}),
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
    ['unifiedjobtemplates', InventorySource(source='ec2')],
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
            reverse('api:credential_detail', kwargs={'pk': cred.pk}),
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
        reverse('api:credential_detail', kwargs={'pk': cred.pk}),
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
            reverse('api:credential_detail', kwargs={'pk': cred.pk}),
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
        reverse('api:credential_detail', kwargs={'pk': cred.pk}),
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
            reverse('api:credential_detail', kwargs={'pk': cred.pk}),
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
        reverse('api:credential_detail', kwargs={'pk': cred.pk}),
        {'name': 'Worst credential ever'},
        admin
    )
    assert response.status_code == 200
    assert Credential.objects.get(pk=cred.pk).name == 'Worst credential ever'

    jt.delete()
    response = _change_credential_type()
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('field', ['password', 'ssh_key_data'])
def test_secret_fields_cannot_be_special_encrypted_variable(post, organization, admin, credentialtype_ssh, field):
    params = {
        'name': 'Best credential ever',
        'credential_type': credentialtype_ssh.id,
        'inputs': {
            'username': 'joe',
            field: '$encrypted$',
        },
        'organization': organization.id,
    }
    response = post(reverse('api:credential_list'), params, admin, status=400)
    assert str(response.data['inputs'][0]) == f'$encrypted$ is a reserved keyword, and cannot be used for {field}.'


@pytest.mark.django_db
def test_ssh_unlock_needed(put, organization, admin, credentialtype_ssh):
    params = {
        'name': 'Best credential ever',
        'credential_type': 1,
        'inputs': {
            'username': 'joe',
            'ssh_key_data': '$encrypted$',
        }
    }
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
        reverse('api:credential_detail', kwargs={'pk': cred.pk}),
        params,
        admin
    )
    assert response.status_code == 400
    assert response.data['inputs']['ssh_key_unlock'] == ['must be set when SSH key is encrypted.']


@pytest.mark.django_db
def test_ssh_unlock_not_needed(put, organization, admin, credentialtype_ssh):
    params = {
        'name': 'Best credential ever',
        'credential_type': 1,
        'inputs': {
            'username': 'joe',
            'ssh_key_data': '$encrypted$',
            'ssh_key_unlock': 'superfluous-key-unlock',
        }
    }
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
        reverse('api:credential_detail', kwargs={'pk': cred.pk}),
        params,
        admin
    )
    assert response.status_code == 400
    assert response.data['inputs']['ssh_key_unlock'] == ['should not be set when SSH key is not encrypted.']


@pytest.mark.django_db
def test_ssh_unlock_with_prior_value(put, organization, admin, credentialtype_ssh):
    params = {
        'name': 'Best credential ever',
        'credential_type': 1,
        'inputs': {
            'username': 'joe',
            'ssh_key_data': '$encrypted$',
            'ssh_key_unlock': 'new-unlock',
        }
    }
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
        reverse('api:credential_detail', kwargs={'pk': cred.pk}),
        params,
        admin
    )
    assert response.status_code == 200

    cred = Credential.objects.all()[:1].get()
    assert decrypt_field(cred, 'ssh_key_unlock') == 'new-unlock'


@pytest.mark.django_db
def test_ssh_bad_key_unlock_not_checked(put, organization, admin, credentialtype_ssh):
    params = {
        'name': 'Best credential ever',
        'credential_type': 1,
        'inputs': {
            'username': 'oscar',
            'ssh_key_data': 'invalid-key',
            'ssh_key_unlock': 'unchecked-unlock',
        }
    }
    cred = Credential(
        credential_type=credentialtype_ssh,
        name='Best credential ever',
        organization=organization,
        inputs={
            'username': u'oscar',
            'ssh_key_data': 'invalid-key',
            'ssh_key_unlock': 'unchecked-unlock',
        }
    )
    cred.save()

    params['organization'] = organization.id
    response = put(
        reverse('api:credential_detail', kwargs={'pk': cred.pk}),
        params,
        admin
    )
    assert response.status_code == 400
    assert response.data['inputs']['ssh_key_data'] == ['Invalid certificate or key: invalid-key...']
    assert 'ssh_key_unlock' not in response.data['inputs']


#
# test secret encryption/decryption
#

@pytest.mark.django_db
def test_secret_encryption_on_create(get, post, organization, admin, credentialtype_ssh):
    params = {
        'credential_type': 1,
        'inputs': {
            'username': 'joe',
            'password': 'secret',
        },
        'name': 'Best credential ever',
        'organization': organization.id,
    }
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201

    response = get(reverse('api:credential_list'), admin)
    assert response.status_code == 200
    assert response.data['count'] == 1
    cred = response.data['results'][0]
    assert cred['inputs']['username'] == 'joe'
    assert cred['inputs']['password'] == '$encrypted$'

    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['password'].startswith('$encrypted$UTF8$AES')
    assert decrypt_field(cred, 'password') == 'secret'


@pytest.mark.django_db
def test_secret_encryption_on_update(get, post, patch, organization, admin, credentialtype_ssh):
    params = {'inputs': {'username': 'joe', 'password': 'secret'}}
    response = post(
        reverse('api:credential_list'),
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
        reverse('api:credential_detail', kwargs={'pk': 1}),
        params,
        admin
    )
    assert response.status_code == 200

    response = get(reverse('api:credential_list'), admin)
    assert response.status_code == 200
    assert response.data['count'] == 1
    cred = response.data['results'][0]
    assert cred['inputs']['username'] == 'joe'
    assert cred['inputs']['password'] == '$encrypted$'

    cred = Credential.objects.all()[:1].get()
    assert cred.inputs['password'].startswith('$encrypted$UTF8$AES')
    assert decrypt_field(cred, 'password') == 'secret'


@pytest.mark.django_db
def test_secret_encryption_previous_value(patch, organization, admin, credentialtype_ssh):
    params = {
        'inputs': {
            'username': 'joe',
            'password': '$encrypted$',
        }
    }
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
        reverse('api:credential_detail', kwargs={'pk': cred.pk}),
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
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 201

    response = get(reverse('api:credential_list'), admin)
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


@pytest.mark.django_db
def test_create_credential_missing_user_team_org_xfail(post, admin, credentialtype_ssh):
    params = {'name': 'Some name', 'credential_type': 1, 'inputs': {'username': 'someusername'}}
    # Must specify one of user, team, or organization
    response = post(reverse('api:credential_list'), params, admin)
    assert response.status_code == 400


@pytest.mark.parametrize('url, status, msg', [
    ('foo.com', 400, 'Invalid URL: Missing url scheme (http, https, etc.)'),
    ('https://[dead:beef', 400, 'Invalid IPv6 URL'),
    ('http:domain:8080', 400, 'Invalid URL: http:domain:8080'),
    ('http:/domain:8080', 400, 'Invalid URL: http:/domain:8080'),
    ('http://foo.com', 201, None)
])
@pytest.mark.django_db
def test_create_credential_with_invalid_url_xfail(post, organization, admin, url, status, msg):
    credential_type = CredentialType(
        kind='test',
        name='MyTestCredentialType',
        inputs = {
            'fields': [{
                'id': 'server_url',
                'label': 'Server Url',
                'type': 'string',
                'format': 'url'
            }]
        }
    )
    credential_type.save()

    params = {
        'name': 'Second Best Credential Ever',
        'organization': organization.pk,
        'credential_type': credential_type.pk,
        'inputs': {'server_url': url}
    }
    endpoint = reverse('api:credential_list')
    response = post(endpoint, params, admin)
    assert response.status_code == status
    if status != 201:
        assert response.data['inputs']['server_url'] == [msg]


@pytest.mark.django_db
def test_external_credential_rbac_test_endpoint(post, alice, external_credential):
    url = reverse('api:credential_external_test', kwargs={'pk': external_credential.pk})
    data = {'metadata': {'key': 'some_key'}}

    external_credential.read_role.members.add(alice)
    assert post(url, data, alice).status_code == 403

    external_credential.use_role.members.add(alice)
    assert post(url, data, alice).status_code == 202
