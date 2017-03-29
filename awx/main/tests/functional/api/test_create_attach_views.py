import pytest

from awx.api.versioning import reverse


@pytest.mark.django_db
def test_user_role_view_access(rando, inventory, mocker, post):
    "Assure correct access method is called when assigning users new roles"
    role_pk = inventory.admin_role.pk
    data = {"id": role_pk}
    mock_access = mocker.MagicMock(can_attach=mocker.MagicMock(return_value=False))
    with mocker.patch('awx.main.access.RoleAccess', return_value=mock_access):
        post(url=reverse('api:user_roles_list', kwargs={'pk': rando.pk}),
             data=data, user=rando, expect=403)
    mock_access.can_attach.assert_called_once_with(
        inventory.admin_role, rando, 'members', data,
        skip_sub_obj_read_check=False)


@pytest.mark.django_db
def test_team_role_view_access(rando, team, inventory, mocker, post):
    "Assure correct access method is called when assigning teams new roles"
    team.admin_role.members.add(rando)
    role_pk = inventory.admin_role.pk
    data = {"id": role_pk}
    mock_access = mocker.MagicMock(can_attach=mocker.MagicMock(return_value=False))
    with mocker.patch('awx.main.access.RoleAccess', return_value=mock_access):
        post(url=reverse('api:team_roles_list', kwargs={'pk': team.pk}),
             data=data, user=rando, expect=403)
    mock_access.can_attach.assert_called_once_with(
        inventory.admin_role, team, 'member_role.parents', data,
        skip_sub_obj_read_check=False)


@pytest.mark.django_db
def test_role_team_view_access(rando, team, inventory, mocker, post):
    """Assure that /role/N/teams/ enforces the same permission restrictions
    that /teams/N/roles/ does when assigning teams new roles"""
    role_pk = inventory.admin_role.pk
    data = {"id": team.pk}
    mock_access = mocker.MagicMock(return_value=False, __name__='mocked')
    with mocker.patch('awx.main.access.RoleAccess.can_attach', mock_access):
        post(url=reverse('api:role_teams_list', kwargs={'pk': role_pk}),
             data=data, user=rando, expect=403)
    mock_access.assert_called_once_with(
        inventory.admin_role, team, 'member_role.parents', data,
        skip_sub_obj_read_check=False)


@pytest.mark.django_db
def test_org_associate_with_junk_data(rando, admin_user, organization, post):
    """
    Assure that post-hoc enforcement of auditor role
    will turn off if the action is an association
    """
    user_data = {'is_system_auditor': True, 'id': rando.pk}
    post(url=reverse('api:organization_users_list', kwargs={'pk': organization.pk}),
         data=user_data, expect=204, user=admin_user)
    # assure user is now an org member
    assert rando in organization.member_role
    # assure that this did not also make them a system auditor
    assert not rando.is_system_auditor
