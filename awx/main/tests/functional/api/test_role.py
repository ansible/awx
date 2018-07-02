import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
def test_admin_visible_to_orphaned_users(get, alice):
    names = set()

    response = get(reverse('api:role_list'), user=alice)
    for item in response.data['results']:
        names.add(item['name'])
    assert 'System Auditor' in names
    assert 'System Administrator' in names


@pytest.mark.django_db
@pytest.mark.parametrize('role,code', [
    ('member_role', 400),
    ('admin_role', 400),
    ('inventory_admin_role', 204)
])
@pytest.mark.parametrize('reversed', [
    True, False
])
def test_org_object_role_assigned_to_team(post, team, organization, org_admin, role, code, reversed):
    if reversed:
        url = reverse('api:role_teams_list', kwargs={'pk': getattr(organization, role).id})
        sub_id = team.id
    else:
        url = reverse('api:team_roles_list', kwargs={'pk': team.id})
        sub_id = getattr(organization, role).id

    post(
        url=url,
        data={'id': sub_id},
        user=org_admin,
        expect=code
    )
