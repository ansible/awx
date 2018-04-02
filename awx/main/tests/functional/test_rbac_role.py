import pytest

from awx.main.access import (
    RoleAccess,
    UserAccess,
    TeamAccess)
from awx.main.models import Role


@pytest.mark.django_db
def test_team_access_attach(rando, team, inventory):
    # rando is admin of the team
    team.admin_role.members.add(rando)
    inventory.read_role.members.add(rando)
    # team has read_role for the inventory
    team.member_role.children.add(inventory.read_role)

    access = TeamAccess(rando)
    data = {'id': inventory.admin_role.pk}
    assert not access.can_attach(team, inventory.admin_role, 'member_role.children', data, False)


@pytest.mark.django_db
def test_user_access_attach(rando, inventory):
    inventory.read_role.members.add(rando)
    access = UserAccess(rando)
    data = {'id': inventory.admin_role.pk}
    assert not access.can_attach(rando, inventory.admin_role, 'roles', data, False)


@pytest.mark.django_db
def test_role_access_attach(rando, inventory):
    inventory.read_role.members.add(rando)
    access = RoleAccess(rando)
    assert not access.can_attach(inventory.admin_role, rando, 'members', None)


@pytest.mark.django_db
def test_visible_roles(admin_user, system_auditor, rando, organization, project):
    '''
    system admin & system auditor fixtures needed to create system roles
    '''
    organization.auditor_role.members.add(rando)
    access = RoleAccess(rando)

    assert rando not in organization.admin_role
    assert access.can_read(organization.admin_role)
    assert organization.admin_role in Role.visible_roles(rando)

    assert rando not in project.admin_role
    assert access.can_read(project.admin_role)
    assert project.admin_role in Role.visible_roles(rando)


@pytest.mark.django_db
def test_org_user_role_attach(user, organization):
    admin = user('admin')
    nonmember = user('nonmember')

    organization.admin_role.members.add(admin)

    access = RoleAccess(admin)
    assert not access.can_attach(organization.member_role, nonmember, 'members', None)
