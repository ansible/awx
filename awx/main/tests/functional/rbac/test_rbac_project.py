import pytest

from ansible_base.rbac import permission_registry
from ansible_base.rbac.models import RoleDefinition
from awx.main.access import (
    ProjectAccess,
)


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["admin_role", "project_admin_role"])
def test_access_admin(role, organization, project, user):
    a = user('admin', False)
    project.organization = organization

    role = getattr(organization, role)
    role.members.add(a)

    access = ProjectAccess(a)
    assert access.can_read(project)
    assert access.can_add(None)
    assert access.can_add({'organization': organization.id})
    assert access.can_change(project, None)
    assert access.can_change(project, {'organization': organization.id})
    assert access.can_admin(project, None)
    assert access.can_admin(project, {'organization': organization.id})
    assert access.can_delete(project)


@pytest.mark.django_db
def test_project_delete_requires_delete_permission(project, rando, setup_managed_roles):
    content_type = permission_registry.content_type_model.objects.get_for_model(project)
    change_role = RoleDefinition.objects.create_from_permissions(
        name='project-change-only',
        permissions=['view_project', 'change_project'],
        content_type=content_type,
    )
    delete_role = RoleDefinition.objects.create_from_permissions(
        name='project-delete',
        permissions=['view_project', 'change_project', 'delete_project'],
        content_type=content_type,
    )

    change_role.give_permission(rando, project)
    access = ProjectAccess(rando)
    assert rando.has_obj_perm(project, 'change')
    assert not rando.has_obj_perm(project, 'delete')
    assert not access.can_delete(project)

    delete_role.give_permission(rando, project)
    assert access.can_delete(project)
