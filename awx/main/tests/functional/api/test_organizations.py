# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import pytest
import mock


# Django
from awx.api.versioning import reverse

# AWX
from awx.main.models import * # noqa


@pytest.mark.django_db
def test_organization_list_access_tests(options, head, get, admin, alice):
    options(reverse('api:organization_list'), user=admin, expect=200)
    head(reverse('api:organization_list'), user=admin, expect=200)
    get(reverse('api:organization_list'), user=admin, expect=200)
    options(reverse('api:organization_list'), user=alice, expect=200)
    head(reverse('api:organization_list'), user=alice, expect=200)
    get(reverse('api:organization_list'), user=alice, expect=200)
    options(reverse('api:organization_list'), user=None, expect=401)
    head(reverse('api:organization_list'), user=None, expect=401)
    get(reverse('api:organization_list'), user=None, expect=401)


@pytest.mark.django_db
def test_organization_access_tests(organization, get, admin, alice, bob):
    organization.member_role.members.add(alice)
    get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=admin, expect=200)
    get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=alice, expect=200)
    get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=bob, expect=403)
    get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=None, expect=401)


@pytest.mark.django_db
def test_organization_list_integrity(organization, get, admin, alice):
    res = get(reverse('api:organization_list'), user=admin)
    for field in ['id', 'url', 'name', 'description', 'created']:
        assert field in res.data['results'][0]


@pytest.mark.django_db
def test_organization_list_visibility(organizations, get, admin, alice):
    orgs = organizations(2)

    res = get(reverse('api:organization_list'), user=admin)
    assert res.data['count'] == 2
    assert len(res.data['results']) == 2

    res = get(reverse('api:organization_list'), user=alice)
    assert res.data['count'] == 0

    orgs[1].member_role.members.add(alice)

    res = get(reverse('api:organization_list'), user=alice)
    assert res.data['count'] == 1
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['id'] == orgs[1].id


@pytest.mark.django_db
def test_organization_project_list(organization, project_factory, get, alice, bob, rando):
    prj1 = project_factory('project-one')
    project_factory('project-two')
    organization.admin_role.members.add(alice)
    organization.member_role.members.add(bob)
    prj1.use_role.members.add(bob)
    assert get(reverse('api:organization_projects_list', kwargs={'pk': organization.id}), user=alice).data['count'] == 2
    assert get(reverse('api:organization_projects_list', kwargs={'pk': organization.id}), user=bob).data['count'] == 1
    assert get(reverse('api:organization_projects_list', kwargs={'pk': organization.id}), user=rando).status_code == 403


@pytest.mark.django_db
def test_organization_user_list(organization, get, admin, alice, bob):
    organization.admin_role.members.add(alice)
    organization.member_role.members.add(alice)
    organization.member_role.members.add(bob)
    assert get(reverse('api:organization_users_list', kwargs={'pk': organization.id}), user=admin).data['count'] == 2
    assert get(reverse('api:organization_users_list', kwargs={'pk': organization.id}), user=alice).data['count'] == 2
    assert get(reverse('api:organization_users_list', kwargs={'pk': organization.id}), user=bob).data['count'] == 2
    assert get(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), user=admin).data['count'] == 1
    assert get(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), user=alice).data['count'] == 1
    assert get(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), user=bob).data['count'] == 1


@pytest.mark.django_db
def test_organization_inventory_list(organization, inventory_factory, get, alice, bob, rando):
    inv1 = inventory_factory('inventory-one')
    inventory_factory('inventory-two')
    organization.admin_role.members.add(alice)
    organization.member_role.members.add(bob)
    inv1.use_role.members.add(bob)
    assert get(reverse('api:organization_inventories_list', kwargs={'pk': organization.id}), user=alice).data['count'] == 2
    assert get(reverse('api:organization_inventories_list', kwargs={'pk': organization.id}), user=bob).data['count'] == 1
    get(reverse('api:organization_inventories_list', kwargs={'pk': organization.id}), user=rando, expect=403)


@pytest.mark.django_db
@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
def test_create_organization(post, admin, alice):
    new_org = {
        'name': 'new org',
        'description': 'my description'
    }
    res = post(reverse('api:organization_list'), new_org, user=admin, expect=201)
    assert res.data['name'] == new_org['name']
    res = post(reverse('api:organization_list'), new_org, user=admin, expect=400)


@pytest.mark.django_db
@mock.patch('awx.api.views.feature_enabled', lambda feature: True)
def test_create_organization_xfail(post, alice):
    new_org = {
        'name': 'new org',
        'description': 'my description'
    }
    post(reverse('api:organization_list'), new_org, user=alice, expect=403)


@pytest.mark.django_db
def test_add_user_to_organization(post, organization, alice, bob):
    organization.admin_role.members.add(alice)
    post(reverse('api:organization_users_list', kwargs={'pk': organization.id}), {'id': bob.id}, user=alice, expect=204)
    assert bob in organization.member_role
    post(reverse('api:organization_users_list', kwargs={'pk': organization.id}), {'id': bob.id, 'disassociate': True} , user=alice, expect=204)
    assert bob not in organization.member_role


@pytest.mark.django_db
def test_add_user_to_organization_xfail(post, organization, alice, bob):
    organization.member_role.members.add(alice)
    post(reverse('api:organization_users_list', kwargs={'pk': organization.id}), {'id': bob.id}, user=alice, expect=403)


@pytest.mark.django_db
def test_add_admin_to_organization(post, organization, alice, bob):
    organization.admin_role.members.add(alice)
    post(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), {'id': bob.id}, user=alice, expect=204)
    assert bob in organization.admin_role
    assert bob in organization.member_role
    post(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), {'id': bob.id, 'disassociate': True} , user=alice, expect=204)
    assert bob not in organization.admin_role
    assert bob not in organization.member_role


@pytest.mark.django_db
def test_add_admin_to_organization_xfail(post, organization, alice, bob):
    organization.member_role.members.add(alice)
    post(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), {'id': bob.id}, user=alice, expect=403)


@pytest.mark.django_db
def test_update_organization(get, put, organization, alice, bob):
    organization.admin_role.members.add(alice)
    data = get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=alice, expect=200).data
    data['description'] = 'hi'
    put(reverse('api:organization_detail', kwargs={'pk': organization.id}), data, user=alice, expect=200)
    organization.refresh_from_db()
    assert organization.description == 'hi'
    data['description'] = 'bye'
    put(reverse('api:organization_detail', kwargs={'pk': organization.id}), data, user=bob, expect=403)


@pytest.mark.django_db
@mock.patch('awx.main.access.BaseAccess.check_license', lambda *a, **kw: True)
def test_delete_organization(delete, organization, admin):
    delete(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=admin, expect=204)


@pytest.mark.django_db
@mock.patch('awx.main.access.BaseAccess.check_license', lambda *a, **kw: True)
def test_delete_organization2(delete, organization, alice):
    organization.admin_role.members.add(alice)
    delete(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=alice, expect=204)


@pytest.mark.django_db
@mock.patch('awx.main.access.BaseAccess.check_license', lambda *a, **kw: True)
def test_delete_organization_xfail1(delete, organization, alice):
    organization.member_role.members.add(alice)
    delete(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=alice, expect=403)


@pytest.mark.django_db
@mock.patch('awx.main.access.BaseAccess.check_license', lambda *a, **kw: True)
def test_delete_organization_xfail2(delete, organization):
    delete(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=None, expect=401)
