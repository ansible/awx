import mock
import pytest

from awx.main.access import (
    RoleAccess,
    UserAccess
)

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_user_role_access_view(rando, inventory, mocker, post):
    # rando has read access for the inventory
    inventory.read_role.members.add(rando)

    role_pk = inventory.admin_role.pk
    mock_access = mocker.MagicMock(spec=RoleAccess, can_attach=mock.MagicMock(return_value=False))
    with mocker.patch('awx.main.access.RoleAccess', return_value=mock_access):
        response = post(url=reverse('api:user_roles_list', args=(rando.pk,)),
                        data={'id': role_pk}, user=rando)
    mock_access.can_attach.assert_called_once_with(
        inventory.admin_role, rando, 'members', {"id": role_pk},
        skip_sub_obj_read_check=False)
    assert rando not in inventory.admin_role

@pytest.mark.django_db
def test_role_team_access_view(rando, team, inventory, mocker, post):
    # rando is admin of the team
    team.admin_role.members.add(rando)
    # team has read_role for the inventory
    team.member_role.children.add(inventory.read_role)
    
    role_pk = inventory.admin_role.pk
    mock_access = mocker.MagicMock(spec=RoleAccess)
    with mocker.patch('awx.main.access.RoleAccess', return_value=mock_access):
        response = post(url=reverse('api:role_teams_list', args=(role_pk,)),
                        data={'id': team.pk}, user=rando)
    mock_access.can_attach.assert_called_once_with(
        inventory.admin_role, team, 'members', {"id": role_pk},
        skip_sub_obj_read_check=False)
    assert team not in inventory.admin_role

@pytest.mark.django_db
def test_inventory_read_role_user_can_access(rando, inventory):
    inventory.read_role.members.add(rando)
    access = RoleAccess(rando)
    assert not rando.can_access(
        User, 'attach', rando, inventory.admin_role, 'roles',
        {'id': inventory.admin_role.pk}, False)

@pytest.mark.django_db
def test_inventory_read_role_user_access(rando, inventory):
    inventory.read_role.members.add(rando)
    access = UserAccess(rando)
    data = {'id': inventory.admin_role.pk}
    assert not access.can_attach(rando, inventory.admin_role, 'roles', data, False)

@pytest.mark.django_db
def test_inventory_read_role_access(rando, inventory):
    inventory.read_role.members.add(rando)
    access = RoleAccess(rando)
    assert not access.can_attach(inventory.admin_role, rando, 'members', None)

