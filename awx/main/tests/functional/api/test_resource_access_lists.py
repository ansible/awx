import pytest

from awx.api.versioning import reverse
from awx.main.models import Role


@pytest.mark.django_db
def test_indirect_access_list(get, organization, project, team_factory, user, admin):
    project_admin = user('project_admin')
    project_admin_team_member = user('project_admin_team_member')

    team_admin = user('team_admin')

    project_admin_team = team_factory('project-admin-team')

    project.admin_role.members.add(project_admin)
    project_admin_team.member_role.members.add(project_admin_team_member)
    project_admin_team.member_role.children.add(project.admin_role)

    project_admin_team.admin_role.members.add(team_admin)

    result = get(reverse('api:project_access_list', kwargs={'pk': project.id}), admin)
    assert result.status_code == 200

    # Result should be:
    #   project_admin should have direct access,
    #   project_team_admin should have "direct" access through being a team member -> project admin,
    #   team_admin should have direct access the same as the project_team_admin,
    #   admin should have access through system admin -> org admin -> project admin
    assert result.data['count'] == 4

    project_admin_res = [r for r in result.data['results'] if r['id'] == project_admin.id][0]
    team_admin_res = [r for r in result.data['results'] if r['id'] == team_admin.id][0]
    project_admin_team_member_res   = [r for r in result.data['results'] if r['id'] == project_admin_team_member.id][0]
    admin_res = [r for r in result.data['results'] if r['id'] == admin.id][0]

    assert len(project_admin_res['summary_fields']['direct_access']) == 1
    assert len(project_admin_res['summary_fields']['indirect_access']) == 0
    assert len(team_admin_res['summary_fields']['direct_access']) == 1
    assert len(team_admin_res['summary_fields']['indirect_access']) == 0
    assert len(admin_res['summary_fields']['direct_access']) == 0
    assert len(admin_res['summary_fields']['indirect_access']) == 1

    project_admin_entry = project_admin_res['summary_fields']['direct_access'][0]['role']
    assert project_admin_entry['id'] == project.admin_role.id
    # assure that results for team admin are the same as for team member
    team_admin_entry = team_admin_res['summary_fields']['direct_access'][0]['role']
    assert team_admin_entry['id'] == project.admin_role.id
    assert team_admin_entry['name'] == 'Admin'

    project_admin_team_member_entry = project_admin_team_member_res['summary_fields']['direct_access'][0]['role']
    assert project_admin_team_member_entry['id'] == project.admin_role.id
    assert project_admin_team_member_entry['team_id'] == project_admin_team.id
    assert project_admin_team_member_entry['team_name'] == project_admin_team.name

    admin_entry = admin_res['summary_fields']['indirect_access'][0]['role']
    assert admin_entry['name'] == Role.singleton('system_administrator').name

