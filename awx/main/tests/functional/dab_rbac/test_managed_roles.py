import pytest

from ansible_base.rbac.models import RoleDefinition, DABPermission


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
