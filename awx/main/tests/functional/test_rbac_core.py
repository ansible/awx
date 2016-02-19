import pytest

from awx.main.models import (
    Role,
    Organization,
)


@pytest.mark.django_db
def test_auto_inheritance_by_children(organization, alice):
    A = Role.objects.create(name='A')
    B = Role.objects.create(name='B')
    A.members.add(alice)

    assert organization.accessible_by(alice, {'read': True}) is False
    A.children.add(B)
    assert organization.accessible_by(alice, {'read': True}) is False
    A.children.add(organization.admin_role)
    assert organization.accessible_by(alice, {'read': True}) is True
    A.children.remove(organization.admin_role)
    assert organization.accessible_by(alice, {'read': True}) is False
    B.children.add(organization.admin_role)
    assert organization.accessible_by(alice, {'read': True}) is True
    B.children.remove(organization.admin_role)
    assert organization.accessible_by(alice, {'read': True}) is False


@pytest.mark.django_db
def test_auto_inheritance_by_parents(organization, alice):
    A = Role.objects.create(name='A')
    B = Role.objects.create(name='B')
    A.members.add(alice)

    assert organization.accessible_by(alice, {'read': True}) is False
    B.parents.add(A)
    assert organization.accessible_by(alice, {'read': True}) is False
    organization.admin_role.parents.add(A)
    assert organization.accessible_by(alice, {'read': True}) is True
    organization.admin_role.parents.remove(A)
    assert organization.accessible_by(alice, {'read': True}) is False
    organization.admin_role.parents.add(B)
    assert organization.accessible_by(alice, {'read': True}) is True
    organization.admin_role.parents.remove(B)
    assert organization.accessible_by(alice, {'read': True}) is False


@pytest.mark.django_db
def test_permission_union(organization, alice):
    A = Role.objects.create(name='A')
    A.members.add(alice)
    B = Role.objects.create(name='B')
    B.members.add(alice)

    assert organization.accessible_by(alice, {'read': True, 'write': True}) is False
    A.grant(organization, {'read': True})
    assert organization.accessible_by(alice, {'read': True, 'write': True}) is False
    B.grant(organization, {'write': True})
    assert organization.accessible_by(alice, {'read': True, 'write': True}) is True


@pytest.mark.django_db
def test_team_symantics(organization, team, alice):
    assert organization.accessible_by(alice, {'read': True}) is False
    team.member_role.children.add(organization.auditor_role)
    assert organization.accessible_by(alice, {'read': True}) is False
    team.users.add(alice)
    assert organization.accessible_by(alice, {'read': True}) is True
    team.users.remove(alice)
    assert organization.accessible_by(alice, {'read': True}) is False
    alice.teams.add(team)
    assert organization.accessible_by(alice, {'read': True}) is True
    alice.teams.remove(team)
    assert organization.accessible_by(alice, {'read': True}) is False


@pytest.mark.django_db
def test_auto_m2m_adjuments(organization, project, alice):
    'Ensures the auto role reparenting is working correctly through m2m maps'
    organization.admin_role.members.add(alice)
    assert project.accessible_by(alice, {'read': True}) is True

    project.organizations.remove(organization)
    assert project.accessible_by(alice, {'read': True}) is False
    project.organizations.add(organization)
    assert project.accessible_by(alice, {'read': True}) is True

    organization.projects.remove(project)
    assert project.accessible_by(alice, {'read': True}) is False
    organization.projects.add(project)
    assert project.accessible_by(alice, {'read': True}) is True

@pytest.mark.django_db
@pytest.mark.skipif(True, reason='Unimplemented')
def test_auto_field_adjuments(organization, inventory, team, alice):
    'Ensures the auto role reparenting is working correctly through m2m maps'
    org2 = Organization.objects.create(name='Org 2', description='org 2')
    org2.admin_role.members.add(alice)
    assert inventory.accessible_by(alice, {'read': True}) is False
    inventory.organization = org2
    assert inventory.accessible_by(alice, {'read': True}) is True
    inventory.organization = organization
    assert inventory.accessible_by(alice, {'read': True}) is False

