import pytest

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse as django_reverse

from awx.api.versioning import reverse
from awx.main.models import JobTemplate, Inventory, Organization
from awx.main.access import JobTemplateAccess, WorkflowJobTemplateAccess

from ansible_base.rbac.models import RoleDefinition


@pytest.mark.django_db
def test_managed_roles_created(setup_managed_roles):
    "Managed RoleDefinitions are created in post_migration signal, we expect to see them here"
    for cls in (JobTemplate, Inventory):
        ct = ContentType.objects.get_for_model(cls)
        rds = list(RoleDefinition.objects.filter(content_type=ct))
        assert len(rds) > 1
        assert f'{cls.__name__} Admin' in [rd.name for rd in rds]
        for rd in rds:
            assert rd.managed is True


@pytest.mark.django_db
def test_custom_read_role(admin_user, post, setup_managed_roles):
    rd_url = django_reverse('roledefinition-list')
    resp = post(
        url=rd_url, data={"name": "read role made for test", "content_type": "awx.inventory", "permissions": ['view_inventory']}, user=admin_user, expect=201
    )
    rd_id = resp.data['id']
    rd = RoleDefinition.objects.get(id=rd_id)
    assert rd.content_type == ContentType.objects.get_for_model(Inventory)


@pytest.mark.django_db
def test_custom_system_roles_prohibited(admin_user, post):
    rd_url = django_reverse('roledefinition-list')
    resp = post(url=rd_url, data={"name": "read role made for test", "content_type": None, "permissions": ['view_inventory']}, user=admin_user, expect=400)
    assert 'System-wide roles are not enabled' in str(resp.data)


@pytest.mark.django_db
def test_assignment_to_invisible_user(admin_user, alice, rando, inventory, post, setup_managed_roles):
    "Alice can not see rando, and so can not give them a role assignment"
    rd = RoleDefinition.objects.get(name='Inventory Admin')
    rd.give_permission(alice, inventory)
    url = django_reverse('roleuserassignment-list')
    r = post(url=url, data={"user": rando.id, "role_definition": rd.id, "object_id": inventory.id}, user=alice, expect=400)
    assert 'does not exist' in str(r.data)
    assert not rando.has_obj_perm(inventory, 'change')


@pytest.mark.django_db
def test_assign_managed_role(admin_user, alice, rando, inventory, post, setup_managed_roles, organization):
    rd = RoleDefinition.objects.get(name='Inventory Admin')
    rd.give_permission(alice, inventory)
    # When alice and rando are members of the same org, they can see each other
    member_rd = RoleDefinition.objects.get(name='Organization Member')
    for u in (alice, rando):
        member_rd.give_permission(u, organization)
    # Now that alice has full permissions to the inventory, and can see rando, she will give rando permission
    url = django_reverse('roleuserassignment-list')
    post(url=url, data={"user": rando.id, "role_definition": rd.id, "object_id": inventory.id}, user=alice, expect=201)
    assert rando.has_obj_perm(inventory, 'change') is True


@pytest.mark.django_db
def test_assign_custom_delete_role(admin_user, rando, inventory, delete, patch):
    # TODO: just a delete_inventory, without change_inventory
    rd, _ = RoleDefinition.objects.get_or_create(
        name='inventory-delete',
        permissions=['delete_inventory', 'view_inventory', 'change_inventory'],
        content_type=ContentType.objects.get_for_model(Inventory),
    )
    rd.give_permission(rando, inventory)
    inv_id = inventory.pk
    inv_url = reverse('api:inventory_detail', kwargs={'pk': inv_id})
    # TODO: eventually this will be valid test, for now ignore
    # patch(url=inv_url, data={"description": "new"}, user=rando, expect=403)
    delete(url=inv_url, user=rando, expect=202)
    assert Inventory.objects.get(id=inv_id).pending_deletion


@pytest.mark.django_db
def test_assign_custom_add_role(admin_user, rando, organization, post, setup_managed_roles):
    rd, _ = RoleDefinition.objects.get_or_create(
        name='inventory-add', permissions=['add_inventory', 'view_organization'], content_type=ContentType.objects.get_for_model(Organization)
    )
    rd.give_permission(rando, organization)
    url = reverse('api:inventory_list')
    r = post(url=url, data={'name': 'abc', 'organization': organization.id}, user=rando, expect=201)
    inv_id = r.data['id']
    inventory = Inventory.objects.get(id=inv_id)
    assert rando.has_obj_perm(inventory, 'change')


@pytest.mark.django_db
def test_jt_creation_permissions(setup_managed_roles, inventory, project, rando):
    """This tests that if you assign someone required permissions in the new API
    using the managed roles, then that works to give permissions to create a job template"""
    inv_rd = RoleDefinition.objects.get(name='Inventory Admin')
    proj_rd = RoleDefinition.objects.get(name='Project Admin')
    # establish prior state
    access = JobTemplateAccess(rando)
    assert not access.can_add({'inventory': inventory.pk, 'project': project.pk, 'name': 'foo-jt'})

    inv_rd.give_permission(rando, inventory)
    proj_rd.give_permission(rando, project)

    assert access.can_add({'inventory': inventory.pk, 'project': project.pk, 'name': 'foo-jt'})


@pytest.mark.django_db
def test_workflow_creation_permissions(setup_managed_roles, organization, workflow_job_template, rando):
    """Similar to JT, assigning new roles gives creator permissions"""
    org_wf_rd = RoleDefinition.objects.get(name='Organization WorkflowJobTemplate Admin')
    assert workflow_job_template.organization == organization  # sanity
    # establish prior state
    access = WorkflowJobTemplateAccess(rando)
    assert not access.can_add({'name': 'foo-flow', 'organization': organization.pk})
    org_wf_rd.give_permission(rando, organization)

    assert access.can_add({'name': 'foo-flow', 'organization': organization.pk})


@pytest.mark.django_db
def test_assign_credential_to_user_of_another_org(setup_managed_roles, credential, admin_user, rando, org_admin, organization, post):
    '''Test that a credential can only be assigned to a user in the same organization'''
    # cannot assign credential to rando, as rando is not in the same org as the credential
    rd = RoleDefinition.objects.get(name="Credential Admin")
    credential.organization = organization
    credential.save(update_fields=['organization'])
    assert credential.organization not in Organization.access_qs(rando, 'member')
    url = django_reverse('roleuserassignment-list')
    resp = post(url=url, data={"user": rando.id, "role_definition": rd.id, "object_id": credential.id}, user=admin_user, expect=400)
    assert "You cannot grant credential access to a User not in the credentials' organization" in str(resp.data)

    # can assign credential to superuser
    rando.is_superuser = True
    rando.save()
    post(url=url, data={"user": rando.id, "role_definition": rd.id, "object_id": credential.id}, user=admin_user, expect=201)

    # can assign credential to org_admin
    assert credential.organization in Organization.access_qs(org_admin, 'member')
    post(url=url, data={"user": org_admin.id, "role_definition": rd.id, "object_id": credential.id}, user=admin_user, expect=201)


@pytest.mark.django_db
def test_team_member_role_not_assignable(team, rando, post, admin_user, setup_managed_roles):
    member_rd = RoleDefinition.objects.get(name='Organization Member')
    url = django_reverse('roleuserassignment-list')
    r = post(url, data={'object_id': team.id, 'role_definition': member_rd.id, 'user': rando.id}, user=admin_user, expect=400)
    assert 'Not managed locally' in str(r.data)


@pytest.mark.django_db
def test_adding_user_to_org_member_role(setup_managed_roles, organization, admin, bob, post, get):
    '''
    Adding user to organization member role via the legacy RBAC endpoints
    should give them access to the organization detail
    '''
    url_detail = reverse('api:organization_detail', kwargs={'pk': organization.id})
    get(url_detail, user=bob, expect=403)

    role = organization.member_role
    url = reverse('api:role_users_list', kwargs={'pk': role.id})
    post(url, data={'id': bob.id}, user=admin, expect=204)

    get(url_detail, user=bob, expect=200)


@pytest.mark.django_db
@pytest.mark.parametrize('actor', ['user', 'team'])
@pytest.mark.parametrize('role_name', ['Organization Admin', 'Organization Member', 'Team Admin', 'Team Member'])
def test_prevent_adding_actor_to_platform_roles(setup_managed_roles, role_name, actor, organization, team, admin, bob, post):
    '''
    Prevent user or team from being added to platform-level roles
    '''
    rd = RoleDefinition.objects.get(name=role_name)
    endpoint = 'roleuserassignment-list' if actor == 'user' else 'roleteamassignment-list'
    url = django_reverse(endpoint)
    object_id = team.id if 'Team' in role_name else organization.id
    data = {'object_id': object_id, 'role_definition': rd.id}
    actor_id = bob.id if actor == 'user' else team.id
    data[actor] = actor_id
    r = post(url, data=data, user=admin, expect=400)
    assert 'Not managed locally' in str(r.data)


@pytest.mark.django_db
@pytest.mark.parametrize('role_name', ['Controller Team Admin', 'Controller Team Member'])
def test_adding_user_to_controller_team_roles(setup_managed_roles, role_name, team, admin, bob, post, get):
    '''
    Allow user to be added to Controller Team Admin or Controller Team Member
    '''
    url_detail = reverse('api:team_detail', kwargs={'pk': team.id})
    get(url_detail, user=bob, expect=403)

    rd = RoleDefinition.objects.get(name=role_name)
    url = django_reverse('roleuserassignment-list')
    post(url, data={'object_id': team.id, 'role_definition': rd.id, 'user': bob.id}, user=admin, expect=201)

    get(url_detail, user=bob, expect=200)


@pytest.mark.django_db
@pytest.mark.parametrize('role_name', ['Controller Organization Admin', 'Controller Organization Member'])
def test_adding_user_to_controller_organization_roles(setup_managed_roles, role_name, organization, admin, bob, post, get):
    '''
    Allow user to be added to Controller Organization Admin or Controller Organization Member
    '''
    url_detail = reverse('api:organization_detail', kwargs={'pk': organization.id})
    get(url_detail, user=bob, expect=403)

    rd = RoleDefinition.objects.get(name=role_name)
    url = django_reverse('roleuserassignment-list')
    post(url, data={'object_id': organization.id, 'role_definition': rd.id, 'user': bob.id}, user=admin, expect=201)

    get(url, user=bob, expect=200)
