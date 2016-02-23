import mock # noqa
import pytest

from django.core.urlresolvers import reverse
from awx.main.models.rbac import Role

def mock_feature_enabled(feature, bypass_database=None):
    return True

#@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)


#
# /roles
#

@pytest.mark.django_db
def test_get_roles_list_admin(organization, get, admin):
    'Admin can see list of all roles'
    url = reverse('api:role_list')
    response = get(url, admin)
    assert response.status_code == 200
    roles = response.data
    assert roles['count'] > 0

@pytest.mark.django_db
@pytest.mark.skipif(True, reason='Unimplemented')
def test_get_roles_list_user(organization, get, user):
    'Users can see all roles they have access to, but not all roles'
    assert False


@pytest.mark.django_db
@pytest.mark.skipif(True, reason='Waiting on custom role requirements')
def test_create_role(post, admin):
    'Admins can create new roles'
    #u = user('admin', True)
    response = post(reverse('api:role_list'), {'name': 'New Role'}, admin)
    assert response.status_code == 201


@pytest.mark.django_db
@pytest.mark.skipif(True, reason='Waiting on custom role requirements')
def test_delete_role(post, admin):
    'Admins can delete a custom role'
    assert False


@pytest.mark.django_db
@pytest.mark.skipif(True, reason='Waiting on custom role requirements')
def test_user_create_role(organization, get, user):
    'User can create custom roles'
    assert False

@pytest.mark.django_db
@pytest.mark.skipif(True, reason='Waiting on custom role requirements')
def test_user_delete_role(organization, get, user):
    'User can delete their custom roles, but not any old row'
    assert False



#
# /user/<id>/roles
#

@pytest.mark.django_db
def test_get_user_roles_list(get, admin):
    url = reverse('api:user_roles_list', args=(admin.id,))
    response = get(url, admin)
    assert response.status_code == 200
    roles = response.data
    assert roles['count'] > 0 # 'System Administrator' role if nothing else

@pytest.mark.django_db
def test_add_role_to_user(role, post, admin):
    assert admin.roles.filter(id=role.id).count() == 0
    url = reverse('api:user_roles_list', args=(admin.id,))

    response = post(url, {'id': role.id}, admin)
    assert response.status_code == 204
    assert admin.roles.filter(id=role.id).count() == 1

    response = post(url, {'id': role.id}, admin)
    assert response.status_code == 204
    assert admin.roles.filter(id=role.id).count() == 1

    response = post(url, {}, admin)
    assert response.status_code == 400
    assert admin.roles.filter(id=role.id).count() == 1

@pytest.mark.django_db
def test_remove_role_from_user(role, post, admin):
    assert admin.roles.filter(id=role.id).count() == 0
    url = reverse('api:user_roles_list', args=(admin.id,))
    response = post(url, {'id': role.id}, admin)
    assert response.status_code == 204
    assert admin.roles.filter(id=role.id).count() == 1

    response = post(url, {'disassociate': role.id, 'id': role.id}, admin)
    assert response.status_code == 204
    assert admin.roles.filter(id=role.id).count() == 0




#
# /team/<id>/roles
#

@pytest.mark.django_db
def test_get_teams_roles_list(get, team, organization, admin):
    team.member_role.children.add(organization.admin_role)
    url = reverse('api:team_roles_list', args=(team.id,))
    response = get(url, admin)
    assert response.status_code == 200
    roles = response.data
    assert roles['count'] == 1
    assert roles['results'][0]['id'] == organization.admin_role.id


@pytest.mark.django_db
def test_add_role_to_teams(team, role, post, admin):
    assert team.member_role.children.filter(id=role.id).count() == 0
    url = reverse('api:team_roles_list', args=(team.id,))

    response = post(url, {'id': role.id}, admin)
    assert response.status_code == 204
    assert team.member_role.children.filter(id=role.id).count() == 1

    response = post(url, {'id': role.id}, admin)
    assert response.status_code == 204
    assert team.member_role.children.filter(id=role.id).count() == 1

    response = post(url, {}, admin)
    assert response.status_code == 400
    assert team.member_role.children.filter(id=role.id).count() == 1

@pytest.mark.django_db
def test_remove_role_from_teams(team, role, post, admin):
    assert team.member_role.children.filter(id=role.id).count() == 0
    url = reverse('api:team_roles_list', args=(team.id,))
    response = post(url, {'id': role.id}, admin)
    assert response.status_code == 204
    assert team.member_role.children.filter(id=role.id).count() == 1

    response = post(url, {'disassociate': role.id, 'id': role.id}, admin)
    assert response.status_code == 204
    assert team.member_role.children.filter(id=role.id).count() == 0



#
# /roles/<id>/
#

@pytest.mark.django_db
def test_get_role(get, admin, role):
    url = reverse('api:role_detail', args=(role.id,))
    response = get(url, admin)
    assert response.status_code == 200
    assert response.data['id'] == role.id

@pytest.mark.django_db
def test_put_role(put, admin, role):
    url = reverse('api:role_detail', args=(role.id,))
    response = put(url, {'name': 'Some new name'}, admin)
    assert response.status_code == 200
    r = Role.objects.get(id=role.id)
    assert r.name == 'Some new name'

@pytest.mark.django_db
def test_put_role_access_denied(put, alice, admin, role):
    url = reverse('api:role_detail', args=(role.id,))
    response = put(url, {'name': 'Some new name'}, alice)
    assert response.status_code == 403


#
# /roles/<id>/users/
#

@pytest.mark.django_db
def test_get_role_users(get, admin, role):
    role.members.add(admin)
    url = reverse('api:role_users_list', args=(role.id,))
    response = get(url, admin)
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == admin.id

@pytest.mark.django_db
def test_add_user_to_role(post, admin, role):
    url = reverse('api:role_users_list', args=(role.id,))
    assert role.members.filter(id=admin.id).count() == 0
    post(url, {'id': admin.id}, admin)
    assert role.members.filter(id=admin.id).count() == 1

@pytest.mark.django_db
def test_remove_user_to_role(post, admin, role):
    role.members.add(admin)
    url = reverse('api:role_users_list', args=(role.id,))
    assert role.members.filter(id=admin.id).count() == 1
    post(url, {'disassociate': True, 'id': admin.id}, admin)
    assert role.members.filter(id=admin.id).count() == 0

#
# /roles/<id>/teams/
#

@pytest.mark.django_db
def test_get_role_teams(get, team, admin, role):
    role.parents.add(team.member_role)
    url = reverse('api:role_teams_list', args=(role.id,))
    response = get(url, admin)
    print(response.data)
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == team.id


@pytest.mark.django_db
def test_add_team_to_role(post, team, admin, role):
    url = reverse('api:role_teams_list', args=(role.id,))
    assert role.members.filter(id=admin.id).count() == 0
    res = post(url, {'id': team.id}, admin)
    print res.data
    assert res.status_code == 204
    assert role.parents.filter(id=team.member_role.id).count() == 1

@pytest.mark.django_db
def test_remove_team_from_role(post, team, admin, role):
    role.members.add(admin)
    url = reverse('api:role_teams_list', args=(role.id,))
    assert role.members.filter(id=admin.id).count() == 1
    res = post(url, {'disassociate': True, 'id': team.id}, admin)
    print res.data
    assert res.status_code == 204
    assert role.parents.filter(id=team.member_role.id).count() == 0


#
# /roles/<id>/parents/
#

@pytest.mark.django_db
def test_role_parents(get, team, admin, role):
    role.parents.add(team.member_role)
    url = reverse('api:role_parents_list', args=(role.id,))
    response = get(url, admin)
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == team.member_role.id

@pytest.mark.django_db
@pytest.mark.skipif(True, reason='Waiting on custom role requirements')
def test_role_add_parent(post, team, admin, role):
    assert role.parents.count() == 0
    url = reverse('api:role_parents_list', args=(role.id,))
    post(url, {'id': team.member_role.id}, admin)
    assert role.parents.count() == 1

@pytest.mark.django_db
@pytest.mark.skipif(True, reason='Waiting on custom role requirements')
def test_role_remove_parent(post, team, admin, role):
    role.parents.add(team.member_role)
    assert role.parents.count() == 1
    url = reverse('api:role_parents_list', args=(role.id,))
    post(url, {'disassociate': True, 'id': team.member_role.id}, admin)
    assert role.parents.count() == 0

#
# /roles/<id>/children/
#

@pytest.mark.django_db
def test_role_children(get, team, admin, role):
    role.parents.add(team.member_role)
    url = reverse('api:role_children_list', args=(team.member_role.id,))
    response = get(url, admin)
    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['id'] == role.id

@pytest.mark.django_db
@pytest.mark.skipif(True, reason='Waiting on custom role requirements')
def test_role_add_children(post, team, admin, role):
    assert role.children.count() == 0
    url = reverse('api:role_children_list', args=(role.id,))
    post(url, {'id': team.member_role.id}, admin)
    assert role.children.count() == 1

@pytest.mark.django_db
@pytest.mark.skipif(True, reason='Waiting on custom role requirements')
def test_role_remove_children(post, team, admin, role):
    role.children.add(team.member_role)
    assert role.children.count() == 1
    url = reverse('api:role_children_list', args=(role.id,))
    post(url, {'disassociate': True, 'id': team.member_role.id}, admin)
    assert role.children.count() == 0



#
# /resource/<id>/access_list
#

@pytest.mark.django_db
def test_resource_access_list(get, team, admin, role):
    team.users.add(admin)
    url = reverse('api:resource_access_list', args=(team.resource.id,))
    res = get(url, admin)
    assert res.status_code == 200



#
# Generics
#

@pytest.mark.django_db
def test_ensure_rbac_fields_are_present(organization, get, admin):
    url = reverse('api:organization_detail', args=(organization.id,))
    response = get(url, admin)
    assert response.status_code == 200
    org = response.data

    assert 'summary_fields' in org
    assert 'resource_id' in org
    assert org['resource_id'] > 0
    assert org['related']['resource'] != ''
    assert 'roles' in org['summary_fields']

    org_role_response = get(org['summary_fields']['roles']['admin_role']['url'], admin)
    assert org_role_response.status_code == 200
    role = org_role_response.data
    assert role['related']['organization'] == url





@pytest.mark.django_db
def test_ensure_permissions_is_present(organization, get, user):
    #u = user('admin', True)
    url = reverse('api:organization_detail', args=(organization.id,))
    response = get(url, user('admin', True))
    assert response.status_code == 200
    org = response.data

    assert 'summary_fields' in org
    assert 'permissions' in org['summary_fields']
    assert org['summary_fields']['permissions']['read'] > 0

@pytest.mark.django_db
def test_ensure_role_summary_is_present(organization, get, user):
    #u = user('admin', True)
    url = reverse('api:organization_detail', args=(organization.id,))
    response = get(url, user('admin', True))
    assert response.status_code == 200
    org = response.data

    assert 'summary_fields' in org
    assert 'roles' in org['summary_fields']
    assert org['summary_fields']['roles']['admin_role']['id'] > 0
