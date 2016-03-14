import pytest

from awx.main.models import (
    Role,
    RolePermission,
    Organization,
    Group,
)


@pytest.mark.django_db
def test_auto_inheritance_by_children(organization, alice):
    A = Role.objects.create(name='A')
    B = Role.objects.create(name='B')
    A.members.add(alice)



    assert organization.accessible_by(alice, {'read': True}) is False
    assert Organization.accessible_objects(alice, {'read': True}).count() == 0
    A.children.add(B)
    assert organization.accessible_by(alice, {'read': True}) is False
    assert Organization.accessible_objects(alice, {'read': True}).count() == 0
    A.children.add(organization.admin_role)
    assert organization.accessible_by(alice, {'read': True}) is True
    assert Organization.accessible_objects(alice, {'read': True}).count() == 1
    A.children.remove(organization.admin_role)
    assert organization.accessible_by(alice, {'read': True}) is False
    B.children.add(organization.admin_role)
    assert organization.accessible_by(alice, {'read': True}) is True
    B.children.remove(organization.admin_role)
    assert organization.accessible_by(alice, {'read': True}) is False
    assert Organization.accessible_objects(alice, {'read': True}).count() == 0

    # We've had the case where our pre/post save init handlers in our field descriptors
    # end up creating a ton of role objects because of various not-so-obvious issues
    assert Role.objects.count() < 50


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
    RolePermission.objects.create(role=A, resource=organization, read=True)
    assert organization.accessible_by(alice, {'read': True, 'write': True}) is False
    RolePermission.objects.create(role=A, resource=organization, write=True)
    assert organization.accessible_by(alice, {'read': True, 'write': True}) is True


@pytest.mark.django_db
def test_accessible_objects(organization, alice, bob):
    A = Role.objects.create(name='A')
    A.members.add(alice)
    B = Role.objects.create(name='B')
    B.members.add(alice)
    B.members.add(bob)

    assert Organization.accessible_objects(alice, {'read': True, 'write': True}).count() == 0
    RolePermission.objects.create(role=A, resource=organization, read=True)
    assert Organization.accessible_objects(alice, {'read': True, 'write': True}).count() == 0
    assert Organization.accessible_objects(bob, {'read': True, 'write': True}).count() == 0
    RolePermission.objects.create(role=B, resource=organization, write=True)
    assert Organization.accessible_objects(alice, {'read': True, 'write': True}).count() == 1
    assert Organization.accessible_objects(bob, {'read': True, 'write': True}).count() == 0
    assert Organization.accessible_objects(bob, {'read': True, 'write': True}).count() == 0

@pytest.mark.django_db
def test_team_symantics(organization, team, alice):
    assert organization.accessible_by(alice, {'read': True}) is False
    team.member_role.children.add(organization.auditor_role)
    assert organization.accessible_by(alice, {'read': True}) is False
    team.member_role.members.add(alice)
    assert organization.accessible_by(alice, {'read': True}) is True
    team.member_role.members.remove(alice)
    assert organization.accessible_by(alice, {'read': True}) is False

@pytest.mark.django_db
def test_auto_m2m_adjuments(organization, inventory, group, alice):
    'Ensures the auto role reparenting is working correctly through m2m maps'
    g1 = group(name='g1')
    g1.admin_role.members.add(alice)
    assert g1.accessible_by(alice, {'read': True}) is True
    g2 = group(name='g2')
    assert g2.accessible_by(alice, {'read': True}) is False

    g2.parents.add(g1)
    assert g2.accessible_by(alice, {'read': True}) is True
    g2.parents.remove(g1)
    assert g2.accessible_by(alice, {'read': True}) is False

    g1.children.add(g2)
    assert g2.accessible_by(alice, {'read': True}) is True
    g1.children.remove(g2)
    assert g2.accessible_by(alice, {'read': True}) is False


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

    admin_role_id = delorg.admin_role.id
    auditor_role_id = delorg.auditor_role.id

    assert Role.objects.filter(id=admin_role_id).count() == 1
    assert Role.objects.filter(id=auditor_role_id).count() == 1
    n_alice_roles = alice.roles.count()
    n_system_admin_children = Role.singleton('System Administrator').children.count()
    rp = RolePermission.objects.create(role=delorg.admin_role, resource=delorg, read=True)

    delorg.delete()

    assert Role.objects.filter(id=admin_role_id).count() == 0
    assert Role.objects.filter(id=auditor_role_id).count() == 0
    assert alice.roles.count() == (n_alice_roles - 1)
    assert RolePermission.objects.filter(id=rp.id).count() == 0
    assert Role.singleton('System Administrator').children.count() == (n_system_admin_children - 1)

@pytest.mark.django_db
def test_content_object(user):
    'Ensure our content_object stuf seems to be working'

    org = Organization.objects.create(name='test-org')
    assert org.admin_role.content_object.id == org.id

@pytest.mark.django_db
def test_hierarchy_rebuilding():
    'Tests some subdtle cases around role hierarchy rebuilding'

    X = Role.objects.create(name='X')
    A = Role.objects.create(name='A')
    B = Role.objects.create(name='B')
    C = Role.objects.create(name='C')
    D = Role.objects.create(name='D')

    A.children.add(B)
    A.children.add(D)
    B.children.add(C)
    C.children.add(D)

    assert A.is_ancestor_of(D)
    assert X.is_ancestor_of(D) is False

    X.children.add(A)

    assert X.is_ancestor_of(D) is True

    X.children.remove(A)

    # This can be the stickler, the rebuilder needs to ensure that D's role
    # hierarchy is built after both A and C are updated.
    assert X.is_ancestor_of(D) is False


