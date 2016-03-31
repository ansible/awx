import pytest

from awx.main.access import TeamAccess
from awx.main.models import Project

@pytest.mark.django_db
def test_team_access_superuser(team, user):
    team.member_role.members.add(user('member', False))

    access = TeamAccess(user('admin', True))

    assert access.can_add(None)
    assert access.can_change(team, None)
    assert access.can_delete(team)

    t = access.get_queryset()[0]
    assert len(t.member_role.members.all()) == 1
    assert len(t.organization.admin_role.members.all()) == 0

@pytest.mark.django_db
def test_team_access_org_admin(organization, team, user):
    a = user('admin', False)
    organization.admin_role.members.add(a)
    team.organization = organization
    team.save()

    access = TeamAccess(a)
    assert access.can_add({'organization': organization.pk})
    assert access.can_change(team, None)
    assert access.can_delete(team)

    t = access.get_queryset()[0]
    assert len(t.member_role.members.all()) == 0
    assert len(t.organization.admin_role.members.all()) == 1

@pytest.mark.django_db
def test_team_access_member(organization, team, user):
    u = user('member', False)
    team.member_role.members.add(u)
    team.organization = organization
    team.save()

    access = TeamAccess(u)
    assert not access.can_add({'organization': organization.pk})
    assert not access.can_change(team, None)
    assert not access.can_delete(team)

    t = access.get_queryset()[0]
    assert len(t.member_role.members.all()) == 1
    assert len(t.organization.admin_role.members.all()) == 0

@pytest.mark.django_db
def test_team_accessible_by(team, user, project):
    u = user('team_member', False)

    team.member_role.children.add(project.member_role)
    assert project.accessible_by(team, {'read':True})
    assert not project.accessible_by(u, {'read':True})

    team.member_role.members.add(u)
    assert project.accessible_by(u, {'read':True})

@pytest.mark.django_db
def test_team_accessible_objects(team, user, project):
    u = user('team_member', False)

    team.member_role.children.add(project.member_role)
    assert len(Project.accessible_objects(team, {'read':True})) == 1
    assert not Project.accessible_objects(u, {'read':True})

    team.member_role.members.add(u)
    assert len(Project.accessible_objects(u, {'read':True})) == 1

