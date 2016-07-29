import mock
from mock import PropertyMock

import pytest

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

from django.contrib.contenttypes.models import ContentType

from awx.api.views import (
    RoleUsersList,
    UserRolesList,
)

from awx.main.models import (
    User,
    Role,
)

@pytest.mark.parametrize("pk, err", [
    (111, "not change the membership"),
    (1, "may not perform"),
])
def test_user_roles_list_user_admin_role(pk, err):
    with mock.patch('awx.api.views.Role.objects.get') as role_get, \
            mock.patch('awx.api.views.ContentType.objects.get_for_model') as ct_get:

        role_mock = mock.MagicMock(spec=Role, id=1, pk=1)
        content_type_mock = mock.MagicMock(spec=ContentType)
        role_mock.content_type = content_type_mock
        role_get.return_value = role_mock
        ct_get.return_value = content_type_mock

        with mock.patch('awx.api.views.User.admin_role', new_callable=PropertyMock, return_value=role_mock):
            factory = APIRequestFactory()
            view = UserRolesList.as_view()

            user = User(username="root", is_superuser=True)

            request = factory.post("/user/1/roles", {'id':pk}, format="json")
            force_authenticate(request, user)

            response = view(request)
            response.render()

            assert response.status_code == 403
            assert err in response.content

@pytest.mark.parametrize("admin_role, err", [
    (True, "may not perform"),
    (False, "not change the membership"),
])
def test_role_users_list_other_user_admin_role(admin_role, err):
    with mock.patch('awx.api.views.RoleUsersList.get_parent_object') as role_get, \
            mock.patch('awx.api.views.ContentType.objects.get_for_model') as ct_get:

        role_mock = mock.MagicMock(spec=Role, id=1)
        content_type_mock = mock.MagicMock(spec=ContentType)
        role_mock.content_type = content_type_mock
        role_get.return_value = role_mock
        ct_get.return_value = content_type_mock

        user_admin_role = role_mock if admin_role else None
        with mock.patch('awx.api.views.User.admin_role', new_callable=PropertyMock, return_value=user_admin_role):
            factory = APIRequestFactory()
            view = RoleUsersList.as_view()

            user = User(username="root", is_superuser=True, pk=1, id=1)
            request = factory.post("/role/1/users", {'id':1}, format="json")
            force_authenticate(request, user)

            response = view(request)
            response.render()

            assert response.status_code == 403
            assert err in response.content
