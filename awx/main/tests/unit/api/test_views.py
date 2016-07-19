import mock
import pytest

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

from django.contrib.contenttypes.models import ContentType

from awx.api.views import (
    ApiV1RootView,
    TeamRolesList,
    JobTemplateLabelList,
)

from awx.main.models import (
    User,
    Role,
)

@pytest.fixture
def mock_response_new(mocker):
    m = mocker.patch('awx.api.views.Response.__new__')
    m.return_value = m
    return m

class TestApiV1RootView:
    def test_get_endpoints(self, mocker, mock_response_new):
        endpoints = [
            'authtoken',
            'ping',
            'config',
            #'settings',
            'me',
            'dashboard',
            'organizations',
            'users',
            'projects',
            'teams',
            'credentials',
            'inventory',
            'inventory_scripts',
            'inventory_sources',
            'groups',
            'hosts',
            'job_templates',
            'jobs',
            'ad_hoc_commands',
            'system_job_templates',
            'system_jobs',
            'schedules',
            'notification_templates',
            'notifications',
            'labels',
            'unified_job_templates',
            'unified_jobs',
            'activity_stream',
        ]
        view = ApiV1RootView()
        ret = view.get(mocker.MagicMock())

        assert ret == mock_response_new
        data_arg = mock_response_new.mock_calls[0][1][1]
        for endpoint in endpoints:
            assert endpoint in data_arg

class TestJobTemplateLabelList:
    def test_inherited_mixin_unattach(self):
        with mock.patch('awx.api.generics.DeleteLastUnattachLabelMixin.unattach') as mixin_unattach:
            view = JobTemplateLabelList()
            mock_request = mock.MagicMock()
            
            super(JobTemplateLabelList, view).unattach(mock_request, None, None)
            assert mixin_unattach.called_with(mock_request, None, None)

@pytest.mark.parametrize("url", ["/team/1/roles", "/role/1/teams"])
def test_team_roles_list_post_org_roles(url):
    with mock.patch('awx.api.views.Role.objects.get') as role_get, \
            mock.patch('awx.api.views.ContentType.objects.get_for_model') as ct_get:

        role_mock = mock.MagicMock(spec=Role)
        content_type_mock = mock.MagicMock(spec=ContentType)
        role_mock.content_type = content_type_mock
        role_get.return_value = role_mock
        ct_get.return_value = content_type_mock

        factory = APIRequestFactory()
        view = TeamRolesList.as_view()

        request = factory.post(url, {'id':1}, format="json")
        force_authenticate(request, User(username="root", is_superuser=True))

        response = view(request)
        response.render()

        assert response.status_code == 400
        assert 'cannot assign' in response.content

