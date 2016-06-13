import pytest

from django.core.urlresolvers import reverse


@pytest.mark.django_db
def test_user_role_view_access(rando, inventory, mocker, post):
    "Assure correct access method is called when assigning users new roles"
    role_pk = inventory.admin_role.pk
    data = {"id": role_pk}
    mock_access = mocker.MagicMock(can_attach=mocker.MagicMock(return_value=False))
    with mocker.patch('awx.main.access.RoleAccess', return_value=mock_access):
        post(url=reverse('api:user_roles_list', args=(rando.pk,)),
             data=data, user=rando, expect=403)
    mock_access.can_attach.assert_called_once_with(
        inventory.admin_role, rando, 'members', data,
        skip_sub_obj_read_check=False)
    assert rando not in inventory.admin_role

@pytest.mark.django_db
def test_team_role_view_access(rando, team, inventory, mocker, post):
    "Assure correct access method is called when assigning teams new roles"
    team.admin_role.members.add(rando)
    role_pk = inventory.admin_role.pk
    data = {"id": role_pk}
    mock_access = mocker.MagicMock(can_attach=mocker.MagicMock(return_value=False))
    with mocker.patch('awx.main.access.RoleAccess', return_value=mock_access):
        post(url=reverse('api:team_roles_list', args=(team.pk,)),
             data=data, user=rando, expect=403)
    mock_access.can_attach.assert_called_once_with(
        inventory.admin_role, team, 'member_role.parents', data,
        skip_sub_obj_read_check=False)
    assert team not in inventory.admin_role

@pytest.mark.django_db
def test_role_team_view_access(rando, team, inventory, mocker, post):
    """Assure that /role/N/teams/ enforces the same permission restrictions
    that /teams/N/roles/ does when assigning teams new roles"""
    role_pk = inventory.admin_role.pk
    data = {"id": team.pk}
    mock_access = mocker.MagicMock(return_value=False, __name__='mocked')
    with mocker.patch('awx.main.access.RoleAccess.can_attach', mock_access):
        post(url=reverse('api:role_teams_list', args=(role_pk,)),
             data=data, user=rando, expect=403)
    mock_access.assert_called_once_with(
        inventory.admin_role, team, 'member_role.parents', data,
        skip_sub_obj_read_check=False)
    assert team not in inventory.admin_role
