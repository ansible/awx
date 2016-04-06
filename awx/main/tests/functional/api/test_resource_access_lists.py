import pytest

from django.core.urlresolvers import reverse

@pytest.mark.django_db
def test_indirect_access_list(get, organization, project, team, alice, bob, admin):

    project.admin_role.members.add(alice)
    team.member_role.members.add(bob)
    team.member_role.children.add(organization.admin_role)

    result = get(reverse('api:project_access_list', args=(project.id,)), admin)
    assert result.status_code == 200

    # Result should be alice should have direct access, bob should have
    # indirect access through being a team member -> org admin -> project admin,
    # and admin should have access through system admin -> org admin -> project admin
    assert result.data['count'] == 3

    alice_res = [r for r in result.data['results'] if r['id'] == alice.id][0]
    bob_res   = [r for r in result.data['results'] if r['id'] == bob.id][0]
    admin_res = [r for r in result.data['results'] if r['id'] == admin.id][0]

    assert len(alice_res['summary_fields']['direct_access']) == 1
    assert len(alice_res['summary_fields']['indirect_access']) == 0
    assert len(bob_res['summary_fields']['direct_access']) == 0
    assert len(bob_res['summary_fields']['indirect_access']) == 1
    assert len(admin_res['summary_fields']['direct_access']) == 0
    assert len(admin_res['summary_fields']['indirect_access']) == 1

    alice_entry = alice_res['summary_fields']['direct_access'][0]['role']
    assert alice_entry['id'] == project.admin_role.id

    bob_entry = bob_res['summary_fields']['indirect_access'][0]['role']
    assert bob_entry['id'] == organization.admin_role.id
    assert bob_entry['team_id'] == team.id
    assert bob_entry['team_name'] == team.name

    admin_entry = admin_res['summary_fields']['indirect_access'][0]['role']
    assert admin_entry['name'] == 'System Administrator'

