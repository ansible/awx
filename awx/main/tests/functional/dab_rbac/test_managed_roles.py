import pytest

from ansible_base.rbac.models import RoleDefinition, DABPermission, RoleUserAssignment


@pytest.mark.django_db
def test_roles_to_not_create(setup_managed_roles):
    assert RoleDefinition.objects.filter(name='Organization Admin').count() == 1

    SHOULD_NOT_EXIST = ('Organization Organization Admin', 'Organization Team Admin', 'Organization InstanceGroup Admin')

    bad_rds = RoleDefinition.objects.filter(name__in=SHOULD_NOT_EXIST)
    if bad_rds.exists():
        bad_names = list(bad_rds.values_list('name', flat=True))
        raise Exception(f'Found RoleDefinitions that should not exist: {bad_names}')


@pytest.mark.django_db
def test_project_update_role(setup_managed_roles):
    """Role to allow updating a project on the object-level should exist"""
    assert RoleDefinition.objects.filter(name='Project Update').count() == 1


@pytest.mark.django_db
def test_org_child_add_permission(setup_managed_roles):
    for model_name in ('Project', 'NotificationTemplate', 'WorkflowJobTemplate', 'Inventory'):
        rd = RoleDefinition.objects.get(name=f'Organization {model_name} Admin')
        assert 'add_' in str(rd.permissions.values_list('codename', flat=True)), f'The {rd.name} role definition expected to contain add_ permissions'

    # special case for JobTemplate, anyone can create one with use permission to project/inventory
    assert not DABPermission.objects.filter(codename='add_jobtemplate').exists()


@pytest.mark.django_db
def test_controller_specific_roles_have_correct_permissions(setup_managed_roles):
    '''
    Controller specific roles should have the same permissions as the platform roles
    e.g. Controller Team Admin should have same permission set as Team Admin
    '''
    for rd_name in ['Controller Team Admin', 'Controller Team Member', 'Controller Organization Member', 'Controller Organization Admin']:
        rd = RoleDefinition.objects.get(name=rd_name)
        rd_platform = RoleDefinition.objects.get(name=rd_name.split('Controller ')[1])
        assert set(rd.permissions.all()) == set(rd_platform.permissions.all())


@pytest.mark.django_db
@pytest.mark.parametrize('resource_name', ['Team', 'Organization'])
@pytest.mark.parametrize('action', ['Member', 'Admin'])
def test_legacy_RBAC_uses_controller_specific_roles(setup_managed_roles, resource_name, action, team, bob, organization):
    '''
    Assignment to legacy RBAC roles should use controller specific role definitions
    e.g. Controller Team Admin, Controller Team Member, Controller Organization Member, Controller Organization Admin
    '''
    resource = team if resource_name == 'Team' else organization
    if action == 'Member':
        resource.member_role.members.add(bob)
    else:
        resource.admin_role.members.add(bob)
    rd = RoleDefinition.objects.get(name=f'Controller {resource_name} {action}')
    rd_platform = RoleDefinition.objects.get(name=f'{resource_name} {action}')
    assert RoleUserAssignment.objects.filter(role_definition=rd, user=bob, object_id=resource.id).exists()
    assert not RoleUserAssignment.objects.filter(role_definition=rd_platform, user=bob, object_id=resource.id).exists()
