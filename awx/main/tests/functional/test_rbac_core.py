import pytest

from awx.main.models import (
    Role,
    Organization,
    Project,
)
from awx.main.fields import update_role_parentage_for_instance


@pytest.mark.django_db
def test_auto_inheritance_by_children(organization, alice):
    A = Role.objects.create()
    B = Role.objects.create()
    A.members.add(alice)

    assert alice not in organization.admin_role
    assert Organization.accessible_objects(alice, 'admin_role').count() == 0
    A.children.add(B)
    assert alice not in organization.admin_role
    assert Organization.accessible_objects(alice, 'admin_role').count() == 0
    A.children.add(organization.admin_role)
    assert alice in organization.admin_role
    assert Organization.accessible_objects(alice, 'admin_role').count() == 1
    A.children.remove(organization.admin_role)
    assert alice not in organization.admin_role
    B.children.add(organization.admin_role)
    assert alice in organization.admin_role
    B.children.remove(organization.admin_role)
    assert alice not in organization.admin_role
    assert Organization.accessible_objects(alice, 'admin_role').count() == 0

    # We've had the case where our pre/post save init handlers in our field descriptors
    # end up creating a ton of role objects because of various not-so-obvious issues
    assert Role.objects.count() < 50


@pytest.mark.django_db
def test_auto_inheritance_by_parents(organization, alice):
    A = Role.objects.create()
    B = Role.objects.create()
    A.members.add(alice)

    assert alice not in organization.admin_role
    B.parents.add(A)
    assert alice not in organization.admin_role
    organization.admin_role.parents.add(A)
    assert alice in organization.admin_role
    organization.admin_role.parents.remove(A)
    assert alice not in organization.admin_role
    organization.admin_role.parents.add(B)
    assert alice in organization.admin_role
    organization.admin_role.parents.remove(B)
    assert alice not in organization.admin_role


@pytest.mark.django_db
def test_accessible_objects(organization, alice, bob):
    A = Role.objects.create()
    A.members.add(alice)
    B = Role.objects.create()
    B.members.add(alice)
    B.members.add(bob)

    assert Organization.accessible_objects(alice, 'admin_role').count() == 0
    assert Organization.accessible_objects(bob, 'admin_role').count() == 0
    A.children.add(organization.admin_role)
    assert Organization.accessible_objects(alice, 'admin_role').count() == 1
    assert Organization.accessible_objects(bob, 'admin_role').count() == 0


@pytest.mark.django_db
def test_team_symantics(organization, team, alice):
    assert alice not in organization.auditor_role
    team.member_role.children.add(organization.auditor_role)
    assert alice not in organization.auditor_role
    team.member_role.members.add(alice)
    assert alice in organization.auditor_role
    team.member_role.members.remove(alice)
    assert alice not in organization.auditor_role


@pytest.mark.django_db
def test_auto_field_adjustments(organization, inventory, team, alice):
    'Ensures the auto role reparenting is working correctly through non m2m fields'
    org2 = Organization.objects.create(name='Org 2', description='org 2')
    org2.admin_role.members.add(alice)
    assert alice not in inventory.admin_role
    inventory.organization = org2
    inventory.save()
    assert alice in inventory.admin_role
    inventory.organization = organization
    inventory.save()
    assert alice not in inventory.admin_role
    #assert False


@pytest.mark.django_db
def test_implicit_deletes(alice):
    'Ensures implicit resources and roles delete themselves'
    delorg = Organization.objects.create(name='test-org')
    child = Role.objects.create()
    child.parents.add(delorg.admin_role)
    delorg.admin_role.members.add(alice)

    admin_role_id = delorg.admin_role.id
    auditor_role_id = delorg.auditor_role.id

    assert child.ancestors.count() > 1
    assert Role.objects.filter(id=admin_role_id).count() == 1
    assert Role.objects.filter(id=auditor_role_id).count() == 1
    n_alice_roles = alice.roles.count()
    n_system_admin_children = Role.singleton('system_administrator').children.count()

    delorg.delete()

    assert Role.objects.filter(id=admin_role_id).count() == 0
    assert Role.objects.filter(id=auditor_role_id).count() == 0
    assert alice.roles.count() == (n_alice_roles - 1)
    assert Role.singleton('system_administrator').children.count() == (n_system_admin_children - 1)
    assert child.ancestors.count() == 1
    assert child.ancestors.all()[0] == child


@pytest.mark.django_db
def test_content_object(user):
    'Ensure our content_object stuf seems to be working'

    org = Organization.objects.create(name='test-org')
    assert org.admin_role.content_object.id == org.id


@pytest.mark.django_db
def test_hierarchy_rebuilding_multi_path():
    'Tests a subdtle cases around role hierarchy rebuilding when you have multiple paths to the same role of different length'

    X = Role.objects.create()
    A = Role.objects.create()
    B = Role.objects.create()
    C = Role.objects.create()
    D = Role.objects.create()

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


@pytest.mark.django_db
def test_auto_parenting():
    org1 = Organization.objects.create(name='org1')
    org2 = Organization.objects.create(name='org2')

    prj1 = Project.objects.create(name='prj1')
    prj2 = Project.objects.create(name='prj2')

    assert org1.admin_role.is_ancestor_of(prj1.admin_role) is False
    assert org1.admin_role.is_ancestor_of(prj2.admin_role) is False
    assert org2.admin_role.is_ancestor_of(prj1.admin_role) is False
    assert org2.admin_role.is_ancestor_of(prj2.admin_role) is False

    prj1.organization = org1
    prj1.save()

    assert org1.admin_role.is_ancestor_of(prj1.admin_role)
    assert org1.admin_role.is_ancestor_of(prj2.admin_role) is False
    assert org2.admin_role.is_ancestor_of(prj1.admin_role) is False
    assert org2.admin_role.is_ancestor_of(prj2.admin_role) is False

    prj2.organization = org1
    prj2.save()

    assert org1.admin_role.is_ancestor_of(prj1.admin_role)
    assert org1.admin_role.is_ancestor_of(prj2.admin_role)
    assert org2.admin_role.is_ancestor_of(prj1.admin_role) is False
    assert org2.admin_role.is_ancestor_of(prj2.admin_role) is False

    prj1.organization = org2
    prj1.save()

    assert org1.admin_role.is_ancestor_of(prj1.admin_role) is False
    assert org1.admin_role.is_ancestor_of(prj2.admin_role)
    assert org2.admin_role.is_ancestor_of(prj1.admin_role)
    assert org2.admin_role.is_ancestor_of(prj2.admin_role) is False

    prj2.organization = org2
    prj2.save()

    assert org1.admin_role.is_ancestor_of(prj1.admin_role) is False
    assert org1.admin_role.is_ancestor_of(prj2.admin_role) is False
    assert org2.admin_role.is_ancestor_of(prj1.admin_role)
    assert org2.admin_role.is_ancestor_of(prj2.admin_role)


@pytest.mark.django_db
def test_update_parents_keeps_teams(team, project):
    project.update_role.parents.add(team.member_role)
    assert team.member_role in project.update_role  # test prep sanity check
    update_role_parentage_for_instance(project)
    assert team.member_role in project.update_role  # actual assertion
