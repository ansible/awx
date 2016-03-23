import mock # noqa
import pytest

from django.core.urlresolvers import reverse



#
# Project listing and visibility tests
#

@pytest.mark.django_db
def test_user_project_list(get, project_factory, admin, alice, bob):
    'List of projects a user has access to, filtered by projects you can also see'

    alice_project = project_factory('alice project')
    alice_project.admin_role.members.add(alice)

    bob_project = project_factory('bob project')
    bob_project.admin_role.members.add(bob)

    shared_project = project_factory('shared project')
    shared_project.admin_role.members.add(alice)
    shared_project.admin_role.members.add(bob)

    # admins can see all projects
    assert get(reverse('api:user_projects_list', args=(admin.pk,)), admin).data['count'] == 3

    # admins can see everyones projects
    assert get(reverse('api:user_projects_list', args=(alice.pk,)), admin).data['count'] == 2
    assert get(reverse('api:user_projects_list', args=(bob.pk,)), admin).data['count'] == 2

    # users can see their own projects
    assert get(reverse('api:user_projects_list', args=(alice.pk,)), alice).data['count'] == 2

    # alice should only be able to see the shared project when looking at bobs projects
    assert get(reverse('api:user_projects_list', args=(bob.pk,)), alice).data['count'] == 1

    # alice should see all projects they can see when viewing an admin
    assert get(reverse('api:user_projects_list', args=(admin.pk,)), alice).data['count'] == 2


@pytest.mark.django_db
def test_team_project_list(get, project_factory, team_factory, admin, alice, bob):
    'List of projects a team has access to, filtered by projects you can also see'
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

    # admins can see all projects on a team
    assert get(reverse('api:team_projects_list', args=(team1.pk,)), admin).data['count'] == 2
    assert get(reverse('api:team_projects_list', args=(team2.pk,)), admin).data['count'] == 2

    # users can see all projects on teams they are a member of
    assert get(reverse('api:team_projects_list', args=(team1.pk,)), alice).data['count'] == 2

    # alice should not be able to see team2 projects because she doesn't have access to team2
    res = get(reverse('api:team_projects_list', args=(team2.pk,)), alice)
    assert res.status_code == 403
    # but if she does, then she should only see the shared project
    team2.auditor_role.members.add(alice)
    assert get(reverse('api:team_projects_list', args=(team2.pk,)), alice).data['count'] == 1
    team2.auditor_role.members.remove(alice)


    # Test user endpoints first, very similar tests to test_user_project_list
    # but permissions are being derived from team membership instead.

    # admins can see all projects
    assert get(reverse('api:user_projects_list', args=(admin.pk,)), admin).data['count'] == 3

    # admins can see everyones projects
    assert get(reverse('api:user_projects_list', args=(alice.pk,)), admin).data['count'] == 2
    assert get(reverse('api:user_projects_list', args=(bob.pk,)), admin).data['count'] == 2

    # users can see their own projects
    assert get(reverse('api:user_projects_list', args=(alice.pk,)), alice).data['count'] == 2

    # alice should not be able to see bob
    res = get(reverse('api:user_projects_list', args=(bob.pk,)), alice)
    assert res.status_code == 403

    # alice should see all projects they can see when viewing an admin
    assert get(reverse('api:user_projects_list', args=(admin.pk,)), alice).data['count'] == 2

