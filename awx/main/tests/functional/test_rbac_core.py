import pytest

from awx.main.models import (
    Role,
    Resource,
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
def test_auto_field_adjuments(organization, inventory, team, alice):
    'Ensures the auto role reparenting is working correctly through non m2m fields'
    org2 = Organization.objects.create(name='Org 2', description='org 2')
    org2.admin_role.members.add(alice)
    assert inventory.accessible_by(alice, {'read': True}) is False
    inventory.organization = org2
    inventory.save()
    assert inventory.accessible_by(alice, {'read': True}) is True
    inventory.organization = organization
    inventory.save()
    assert inventory.accessible_by(alice, {'read': True}) is False
    #assert False

@pytest.mark.django_db
def test_implicit_deletes(alice):
    'Ensures implicit resources and roles delete themselves'
    delorg = Organization.objects.create(name='test-org')
    delorg.admin_role.members.add(alice)

    resource_id = delorg.resource.id
    admin_role_id = delorg.admin_role.id
    auditor_role_id = delorg.auditor_role.id

    assert Role.objects.filter(id=admin_role_id).count() == 1
    assert Role.objects.filter(id=auditor_role_id).count() == 1
    assert Resource.objects.filter(id=resource_id).count() == 1
    n_alice_roles = alice.roles.count()
    n_system_admin_children = Role.singleton('System Administrator').children.count()

    delorg.delete()

    assert Role.objects.filter(id=admin_role_id).count() == 0
    assert Role.objects.filter(id=auditor_role_id).count() == 0
    assert Resource.objects.filter(id=resource_id).count() == 0
    assert alice.roles.count() == (n_alice_roles - 1)
    assert Role.singleton('System Administrator').children.count() == (n_system_admin_children - 1)

@pytest.mark.django_db
def test_content_object(user):
    'Ensure our conent_object stuf seems to be working'

    print('Creating organization')
    org = Organization.objects.create(name='test-org')
    print('Organizaiton id: %d  resource: %d  admin_role: %d' % (org.id, org.resource.id, org.admin_role.id))
    assert org.resource.content_object.id == org.id
    assert org.admin_role.content_object.id == org.id

