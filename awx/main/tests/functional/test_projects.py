import mock # noqa
import pytest

from django.db import transaction
from django.core.urlresolvers import reverse
from awx.main.models import Project


#
# Project listing and visibility tests
#

@pytest.mark.django_db
def test_user_project_list(get, organization_factory):
    'List of projects a user has access to, filtered by projects you can also see'

    objects = organization_factory('org1',
                                   projects=['alice project', 'bob project', 'shared project'],
                                   superusers=['admin'],
                                   users=['alice', 'bob'],
                                   roles=['alice project.admin_role:alice',
                                          'bob project.admin_role:bob',
                                          'shared project.admin_role:bob',
                                          'shared project.admin_role:alice'])

    assert get(reverse('api:user_projects_list', args=(objects.superusers.admin.pk,)), objects.superusers.admin).data['count'] == 3

    # admins can see everyones projects
    assert get(reverse('api:user_projects_list', args=(objects.users.alice.pk,)), objects.superusers.admin).data['count'] == 2
    assert get(reverse('api:user_projects_list', args=(objects.users.bob.pk,)), objects.superusers.admin).data['count'] == 2

    # users can see their own projects
    assert get(reverse('api:user_projects_list', args=(objects.users.alice.pk,)), objects.users.alice).data['count'] == 2

    # alice should only be able to see the shared project when looking at bobs projects
    assert get(reverse('api:user_projects_list', args=(objects.users.bob.pk,)), objects.users.alice).data['count'] == 1

    # alice should see all projects they can see when viewing an admin
    assert get(reverse('api:user_projects_list', args=(objects.superusers.admin.pk,)), objects.users.alice).data['count'] == 2


def setup_test_team_project_list(project_factory, team_factory, admin, alice, bob):
    team1 = team_factory('team1')
    team2 = team_factory('team2')

    team1_project = project_factory('team1 project')
    team1_project.admin_role.parents.add(team1.member_role)

    team2_project = project_factory('team2 project')
    team2_project.admin_role.parents.add(team2.member_role)

    shared_project = project_factory('shared project')
    shared_project.admin_role.parents.add(team1.member_role)
    shared_project.admin_role.parents.add(team2.member_role)

    team1.member_role.members.add(alice)
    team2.member_role.members.add(bob)
    return team1, team2

@pytest.mark.django_db
def test_team_project_list(get, project_factory, team_factory, admin, alice, bob):
    'List of projects a team has access to, filtered by projects you can also see'
    team1, team2 = setup_test_team_project_list(project_factory, team_factory, admin, alice, bob)

    # admins can see all projects on a team
    assert get(reverse('api:team_projects_list', args=(team1.pk,)), admin).data['count'] == 2
    assert get(reverse('api:team_projects_list', args=(team2.pk,)), admin).data['count'] == 2

    # users can see all projects on teams they are a member of
    assert get(reverse('api:team_projects_list', args=(team1.pk,)), alice).data['count'] == 2

    # but if she does, then she should only see the shared project
    team2.read_role.members.add(alice)
    assert get(reverse('api:team_projects_list', args=(team2.pk,)), alice).data['count'] == 1
    team2.read_role.members.remove(alice)

    # Test user endpoints first, very similar tests to test_user_project_list
    # but permissions are being derived from team membership instead.
    with transaction.atomic():
        res = get(reverse('api:user_projects_list', args=(bob.pk,)), alice)
        assert res.status_code == 403

    # admins can see all projects
    assert get(reverse('api:user_projects_list', args=(admin.pk,)), admin).data['count'] == 3

    # admins can see everyones projects
    assert get(reverse('api:user_projects_list', args=(alice.pk,)), admin).data['count'] == 2
    assert get(reverse('api:user_projects_list', args=(bob.pk,)), admin).data['count'] == 2

    # users can see their own projects
    assert get(reverse('api:user_projects_list', args=(alice.pk,)), alice).data['count'] == 2

    # alice should see all projects they can see when viewing an admin
    assert get(reverse('api:user_projects_list', args=(admin.pk,)), alice).data['count'] == 2

@pytest.mark.django_db
def test_team_project_list_fail1(get, project_factory, team_factory, admin, alice, bob):
    # alice should not be able to see team2 projects because she doesn't have access to team2
    team1, team2 = setup_test_team_project_list(project_factory, team_factory, admin, alice, bob)
    res = get(reverse('api:team_projects_list', args=(team2.pk,)), alice)
    assert res.status_code == 403

@pytest.mark.django_db
def test_team_project_list_fail2(get, project_factory, team_factory, admin, alice, bob):
    team1, team2 = setup_test_team_project_list(project_factory, team_factory, admin, alice, bob)
    # alice should not be able to see bob

@pytest.mark.parametrize("u,expected_status_code", [
    ('rando', 403),
    ('org_member', 403),
    ('org_admin', 201),
    ('admin', 201)
])
@pytest.mark.django_db()
def test_create_project(post, organization, org_admin, org_member, admin, rando, u, expected_status_code):
    if u == 'rando':
        u = rando
    elif u == 'org_member':
        u = org_member
    elif u == 'org_admin':
        u = org_admin
    elif u == 'admin':
        u = admin

    result = post(reverse('api:project_list'), {
        'name': 'Project',
        'organization': organization.id,
    }, u)
    print(result.data)
    assert result.status_code == expected_status_code
    if expected_status_code == 201:
        assert Project.objects.filter(name='Project', organization=organization).exists()
