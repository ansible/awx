import pytest
from unittest import mock

from awx.main.access import TeamAccess
from awx.main.models import Project, Organization, Team


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
def test_team_member_org_role_access_project(team, rando, project, organization):
    team.member_role.members.add(rando)
    assert rando not in project.read_role
    team.member_role.children.add(organization.project_admin_role)
    assert rando in project.admin_role


@pytest.mark.django_db
def test_team_member_org_role_access_workflow(team, rando, workflow_job_template, organization):
    team.member_role.members.add(rando)
    assert rando not in workflow_job_template.read_role
    team.member_role.children.add(organization.workflow_admin_role)
    assert rando in workflow_job_template.admin_role


@pytest.mark.django_db
def test_team_member_org_role_access_inventory(team, rando, inventory, organization):
    team.member_role.members.add(rando)
    assert rando not in inventory.read_role
    team.member_role.children.add(organization.inventory_admin_role)
    assert rando in inventory.admin_role


@pytest.mark.django_db
def test_org_admin_team_access(organization, team, user, project):
    u = user('team_admin', False)
    organization.admin_role.members.add(u)

    team.organization = organization
    team.save()

    team.member_role.children.add(project.use_role)

    assert len(Project.accessible_objects(u, 'use_role')) == 1


@pytest.mark.django_db
@pytest.mark.parametrize('enabled', [True, False])
def test_org_admin_view_all_teams(org_admin, enabled):
    access = TeamAccess(org_admin)
    other_org = Organization.objects.create(name='other-org')
    other_team = Team.objects.create(name='other-team', organization=other_org)
    with mock.patch('awx.main.access.settings') as settings_mock:
        settings_mock.ORG_ADMINS_CAN_SEE_ALL_USERS = enabled
        assert access.can_read(other_team) is enabled
