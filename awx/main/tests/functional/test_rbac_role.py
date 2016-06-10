import mock
import pytest

from awx.main.access import (
    RoleAccess,
    UserAccess
)

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_inventory_read_role_access_functional(rando, inventory, mocker, post):
    inventory.read_role.members.add(rando)
    role_pk = inventory.admin_role.pk

    mock_access = mocker.MagicMock(spec=RoleAccess, id=968)
    with mocker.patch('awx.main.access.RoleAccess', return_value=mock_access):
        response = post(url=reverse('api:user_roles_list', args=(rando.pk,)),
                        data={'id': role_pk}, user=rando)
    mock_access.can_attach.assert_called_once_with(
        inventory.admin_role, rando, 'members', {"id": role_pk},
        skip_sub_obj_read_check=False)

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

