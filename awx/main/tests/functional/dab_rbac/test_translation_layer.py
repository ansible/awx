import pytest

from awx.main.models.rbac import get_role_from_object_role

from ansible_base.rbac.models import RoleUserAssignment


@pytest.mark.django_db
@pytest.mark.parametrize(
    'role_name',
    ['execution_environment_admin_role', 'project_admin_role', 'admin_role', 'auditor_role', 'read_role', 'execute_role', 'notification_admin_role'],
)
def test_round_trip_roles(organization, rando, role_name):
    """
    Make an assignment with the old-style role,
    get the equivelent new role
    get the old role again
    """
    getattr(organization, role_name).members.add(rando)
    assignment = RoleUserAssignment.objects.get(user=rando)
    print(assignment.role_definition.name)
    old_role = get_role_from_object_role(assignment.object_role)
    assert old_role.id == getattr(organization, role_name).id
