import pytest

from awx.main.access import TeamAccess
from awx.main.models import Project


@pytest.mark.django_db
def test_team_attach_unattach(team, user):
    u = user('member', False)
    access = TeamAccess(u)

    team.member_role.members.add(u)
    assert not access.can_attach(team, team.member_role, 'member_role.children', None)
    assert not access.can_unattach(team, team.member_role, 'member_role.children')

    team.admin_role.members.add(u)
    assert access.can_attach(team, team.member_role, 'member_role.children', None)
    assert access.can_unattach(team, team.member_role, 'member_role.children')

    u2 = user('non-member', False)
    access = TeamAccess(u2)
    assert not access.can_attach(team, team.member_role, 'member_role.children', None)
    assert not access.can_unattach(team, team.member_role, 'member_role.chidlren')


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

    team.member_role.children.add(project.use_role)
    assert team in project.read_role
    assert u not in project.read_role

    team.member_role.members.add(u)
    assert u in project.read_role


@pytest.mark.django_db
def test_team_accessible_objects(team, user, project):
    u = user('team_member', False)

    team.member_role.children.add(project.use_role)
    assert len(Project.accessible_objects(team, 'read_role')) == 1
    assert not Project.accessible_objects(u, 'read_role')

    team.member_role.members.add(u)
    assert len(Project.accessible_objects(u, 'read_role')) == 1


@pytest.mark.django_db
def test_team_admin_member_access(team, user, project):
    u = user('team_admin', False)
    team.member_role.children.add(project.use_role)
    team.admin_role.members.add(u)

    assert len(Project.accessible_objects(u, 'use_role')) == 1


@pytest.mark.django_db
def test_org_admin_team_access(organization, team, user, project):
    u = user('team_admin', False)
    organization.admin_role.members.add(u)

    team.organization = organization
    team.save()

    team.member_role.children.add(project.use_role)

    assert len(Project.accessible_objects(u, 'use_role')) == 1
