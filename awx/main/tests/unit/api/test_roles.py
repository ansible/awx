import mock

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

from django.contrib.contenttypes.models import ContentType

from awx.api.views import (
    TeamRolesList,
)

from awx.main.models import (
    User,
    Role,
)


def test_team_roles_list_post_org_roles():
    with mock.patch('awx.api.views.get_object_or_400') as role_get, \
            mock.patch('awx.api.views.ContentType.objects.get_for_model') as ct_get:

        role_mock = mock.MagicMock(spec=Role)
        content_type_mock = mock.MagicMock(spec=ContentType)
        role_mock.content_type = content_type_mock
        role_get.return_value = role_mock
        ct_get.return_value = content_type_mock

        factory = APIRequestFactory()
        view = TeamRolesList.as_view()

        request = factory.post("/team/1/roles", {'id':1}, format="json")
        force_authenticate(request, User(username="root", is_superuser=True))

        response = view(request)
        response.render()

        assert response.status_code == 400
        assert 'cannot assign' in response.content
