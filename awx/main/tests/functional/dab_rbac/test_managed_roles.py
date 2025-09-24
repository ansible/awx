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
def test_org_admin_role(setup_managed_roles):
    rd = RoleDefinition.objects.get(name='Organization Admin')
    codenames = list(rd.permissions.values_list('codename', flat=True))
    assert 'view_inventory' in codenames
    assert 'change_inventory' in codenames


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
@pytest.mark.parametrize('resource_name', ['Team', 'Organization'])
@pytest.mark.parametrize('action', ['Member', 'Admin'])
def test_legacy_RBAC_uses_platform_roles(setup_managed_roles, resource_name, action, team, bob, organization):
    '''
    Assignment to legacy RBAC roles should use platform role definitions
    e.g. Team Admin, Team Member, Organization Member, Organization Admin
    '''
    resource = team if resource_name == 'Team' else organization
    if action == 'Member':
        resource.member_role.members.add(bob)
    else:
        resource.admin_role.members.add(bob)
    rd = RoleDefinition.objects.get(name=f'{resource_name} {action}')
    assert RoleUserAssignment.objects.filter(role_definition=rd, user=bob, object_id=resource.id).exists()
