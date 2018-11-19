import pytest

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
