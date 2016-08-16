import mock # noqa
import pytest

from django.core.urlresolvers import reverse


#
# user credential creation
#

@pytest.mark.django_db
def test_create_user_credential_via_credentials_list(post, get, alice):
    response = post(reverse('api:credential_list'), {
        'user': alice.id,
        'name': 'Some name',
        'username': 'someusername'
    }, alice)
    assert response.status_code == 201

    response = get(reverse('api:credential_list'), alice)
    assert response.status_code == 200
    assert response.data['count'] == 1

@pytest.mark.django_db
def test_credential_validation_error_with_bad_user(post, admin):
    response = post(reverse('api:credential_list'), {
        'user': 'asdf',
        'name': 'Some name',
        'username': 'someusername'
    }, admin)
    assert response.status_code == 400
    assert response.data['user'][0] == 'Incorrect type. Expected pk value, received unicode.'

@pytest.mark.django_db
def test_create_user_credential_via_user_credentials_list(post, get, alice):
    response = post(reverse('api:user_credentials_list', args=(alice.pk,)), {
        'user': alice.pk,
        'name': 'Some name',
        'username': 'someusername',
    }, alice)
    assert response.status_code == 201

    response = get(reverse('api:user_credentials_list', args=(alice.pk,)), alice)
    assert response.status_code == 200
    assert response.data['count'] == 1

@pytest.mark.django_db
def test_create_user_credential_via_credentials_list_xfail(post, alice, bob):
    response = post(reverse('api:credential_list'), {
        'user': bob.id,
        'name': 'Some name',
        'username': 'someusername'
    }, alice)
    assert response.status_code == 403

@pytest.mark.django_db
def test_create_user_credential_via_user_credentials_list_xfail(post, alice, bob):
    response = post(reverse('api:user_credentials_list', args=(bob.pk,)), {
        'user': bob.pk,
        'name': 'Some name',
        'username': 'someusername'
    }, alice)
    assert response.status_code == 403


#
# team credential creation
#

@pytest.mark.django_db
def test_create_team_credential(post, get, team, organization, org_admin, team_member):
    response = post(reverse('api:credential_list'), {
        'team': team.id,
        'organization': organization.id,
        'name': 'Some name',
        'username': 'someusername'
    }, org_admin)
    assert response.status_code == 201

    response = get(reverse('api:team_credentials_list', args=(team.pk,)), team_member)
    assert response.status_code == 200
    assert response.data['count'] == 1

@pytest.mark.django_db
def test_create_team_credential_via_team_credentials_list(post, get, team, org_admin, team_member):
    response = post(reverse('api:team_credentials_list', args=(team.pk,)), {
        'team': team.pk,
        'name': 'Some name',
        'username': 'someusername',
    }, org_admin)
    assert response.status_code == 201

    response = get(reverse('api:team_credentials_list', args=(team.pk,)), team_member)
    assert response.status_code == 200
    assert response.data['count'] == 1

@pytest.mark.django_db
def test_create_team_credential_by_urelated_user_xfail(post, team, organization, alice, team_member):
    response = post(reverse('api:credential_list'), {
        'team': team.id,
        'organization': organization.id,
        'name': 'Some name',
        'username': 'someusername'
    }, alice)
    assert response.status_code == 403

@pytest.mark.django_db
def test_create_team_credential_by_team_member_xfail(post, team, organization, alice, team_member):
    # Members can't add credentials, only org admins.. for now?
    response = post(reverse('api:credential_list'), {
        'team': team.id,
        'organization': organization.id,
        'name': 'Some name',
        'username': 'someusername'
    }, team_member)
    assert response.status_code == 403


#
# Permission granting
#

@pytest.mark.django_db
def test_grant_org_credential_to_org_user_through_role_users(post, credential, organization, org_admin, org_member):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:role_users_list', args=(credential.use_role.id,)), {
        'id': org_member.id
    }, org_admin)
    assert response.status_code == 204

@pytest.mark.django_db
def test_grant_org_credential_to_org_user_through_user_roles(post, credential, organization, org_admin, org_member):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:user_roles_list', args=(org_member.id,)), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 204

@pytest.mark.django_db
def test_grant_org_credential_to_non_org_user_through_role_users(post, credential, organization, org_admin, alice):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:role_users_list', args=(credential.use_role.id,)), {
        'id': alice.id
    }, org_admin)
    assert response.status_code == 400

@pytest.mark.django_db
def test_grant_org_credential_to_non_org_user_through_user_roles(post, credential, organization, org_admin, alice):
    credential.organization = organization
    credential.save()
    response = post(reverse('api:user_roles_list', args=(alice.id,)), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 400

@pytest.mark.django_db
def test_grant_private_credential_to_user_through_role_users(post, credential, alice, bob):
    # normal users can't do this
    credential.admin_role.members.add(alice)
    response = post(reverse('api:role_users_list', args=(credential.use_role.id,)), {
        'id': bob.id
    }, alice)
    assert response.status_code == 400

@pytest.mark.django_db
def test_grant_private_credential_to_org_user_through_role_users(post, credential, org_admin, org_member):
    # org admins can't either
    credential.admin_role.members.add(org_admin)
    response = post(reverse('api:role_users_list', args=(credential.use_role.id,)), {
        'id': org_member.id
    }, org_admin)
    assert response.status_code == 400

@pytest.mark.django_db
def test_sa_grant_private_credential_to_user_through_role_users(post, credential, admin, bob):
    # but system admins can
    response = post(reverse('api:role_users_list', args=(credential.use_role.id,)), {
        'id': bob.id
    }, admin)
    assert response.status_code == 204

@pytest.mark.django_db
def test_grant_private_credential_to_user_through_user_roles(post, credential, alice, bob):
    # normal users can't do this
    credential.admin_role.members.add(alice)
    response = post(reverse('api:user_roles_list', args=(bob.id,)), {
        'id': credential.use_role.id
    }, alice)
    assert response.status_code == 400

@pytest.mark.django_db
def test_grant_private_credential_to_org_user_through_user_roles(post, credential, org_admin, org_member):
    # org admins can't either
    credential.admin_role.members.add(org_admin)
    response = post(reverse('api:user_roles_list', args=(org_member.id,)), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 400

@pytest.mark.django_db
def test_sa_grant_private_credential_to_user_through_user_roles(post, credential, admin, bob):
    # but system admins can
    response = post(reverse('api:user_roles_list', args=(bob.id,)), {
        'id': credential.use_role.id
    }, admin)
    assert response.status_code == 204

@pytest.mark.django_db
def test_grant_org_credential_to_team_through_role_teams(post, credential, organization, org_admin, org_auditor, team):
    assert org_auditor not in credential.read_role
    credential.organization = organization
    credential.save()
    response = post(reverse('api:role_teams_list', args=(credential.use_role.id,)), {
        'id': team.id
    }, org_admin)
    assert response.status_code == 204
    assert org_auditor in credential.read_role

@pytest.mark.django_db
def test_grant_org_credential_to_team_through_team_roles(post, credential, organization, org_admin, org_auditor, team):
    assert org_auditor not in credential.read_role
    credential.organization = organization
    credential.save()
    response = post(reverse('api:team_roles_list', args=(team.id,)), {
        'id': credential.use_role.id
    }, org_admin)
    assert response.status_code == 204
    assert org_auditor in credential.read_role

@pytest.mark.django_db
def test_sa_grant_private_credential_to_team_through_role_teams(post, credential, admin, team):
    # not even a system admin can grant a private cred to a team though
    response = post(reverse('api:role_teams_list', args=(credential.use_role.id,)), {
        'id': team.id
    }, admin)
    assert response.status_code == 400

@pytest.mark.django_db
def test_sa_grant_private_credential_to_team_through_team_roles(post, credential, admin, team):
    # not even a system admin can grant a private cred to a team though
    response = post(reverse('api:role_teams_list', args=(team.id,)), {
        'id': credential.use_role.id
    }, admin)
    assert response.status_code == 400




#
# organization credentials
#

@pytest.mark.django_db
def test_create_org_credential_as_not_admin(post, organization, org_member):
    response = post(reverse('api:credential_list'), {
        'name': 'Some name',
        'username': 'someusername',
        'organization': organization.id,
    }, org_member)
    assert response.status_code == 403

@pytest.mark.django_db
def test_create_org_credential_as_admin(post, organization, org_admin):
    response = post(reverse('api:credential_list'), {
        'name': 'Some name',
        'username': 'someusername',
        'organization': organization.id,
    }, org_admin)
    assert response.status_code == 201

@pytest.mark.django_db
def test_credential_detail(post, get, organization, org_admin):
    response = post(reverse('api:credential_list'), {
        'name': 'Some name',
        'username': 'someusername',
        'organization': organization.id,
    }, org_admin)
    assert response.status_code == 201
    response = get(reverse('api:credential_detail', args=(response.data['id'],)), org_admin)
    assert response.status_code == 200
    summary_fields = response.data['summary_fields']
    assert 'organization' in summary_fields
    related_fields = response.data['related']
    assert 'organization' in related_fields

@pytest.mark.django_db
def test_list_created_org_credentials(post, get, organization, org_admin, org_member):
    response = post(reverse('api:credential_list'), {
        'name': 'Some name',
        'username': 'someusername',
        'organization': organization.id,
    }, org_admin)
    assert response.status_code == 201

    response = get(reverse('api:credential_list'), org_admin)
    assert response.status_code == 200
    assert response.data['count'] == 1

    response = get(reverse('api:credential_list'), org_member)
    assert response.status_code == 200
    assert response.data['count'] == 0

    response = get(reverse('api:organization_credential_list', args=(organization.pk,)), org_admin)
    assert response.status_code == 200
    assert response.data['count'] == 1

    response = get(reverse('api:organization_credential_list', args=(organization.pk,)), org_member)
    assert response.status_code == 200
    assert response.data['count'] == 0



#
# Openstack Credentials
#

@pytest.mark.django_db
def test_openstack_create_ok(post, organization, admin):
    data = {
        'kind': 'openstack',
        'name': 'Best credential ever',
        'username': 'some_user',
        'password': 'some_password',
        'project': 'some_project',
        'host': 'some_host',
        'organization': organization.id,
    }
    response = post(reverse('api:credential_list'), data, admin)
    assert response.status_code == 201

@pytest.mark.django_db
def test_openstack_create_fail_required_fields(post, organization, admin):
    data = {
        'kind': 'openstack',
        'name': 'Best credential ever',
        'organization': organization.id,
    }
    response = post(reverse('api:credential_list'), data, admin)
    assert response.status_code == 400
    assert 'username' in response.data
    assert 'password' in response.data
    assert 'host' in response.data
    assert 'project' in response.data


#
# misc xfail conditions
#

@pytest.mark.django_db
def test_create_credential_missing_user_team_org_xfail(post, admin):
    # Must specify one of user, team, or organization
    response = post(reverse('api:credential_list'), {
        'name': 'Some name',
        'username': 'someusername',
    }, admin)
    assert response.status_code == 400

