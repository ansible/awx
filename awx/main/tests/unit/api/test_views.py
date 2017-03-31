import mock
import pytest

from collections import namedtuple

from awx.api.views import (
    ApiVersionRootView,
    JobTemplateLabelList,
    JobTemplateSurveySpec,
)


@pytest.fixture
def mock_response_new(mocker):
    m = mocker.patch('awx.api.views.Response.__new__')
    m.return_value = m
    return m


class TestApiRootView:
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
            'workflow_job_templates',
            'workflow_jobs',
        ]
        view = ApiVersionRootView()
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


class TestJobTemplateSurveySpec(object):
    @mock.patch('awx.api.views.feature_enabled', lambda feature: True)
    def test_get_password_type(self, mocker, mock_response_new):
        JobTemplate = namedtuple('JobTemplate', 'survey_spec')
        obj = JobTemplate(survey_spec={'spec':[{'type': 'password', 'default': 'my_default'}]})
        with mocker.patch.object(JobTemplateSurveySpec, 'get_object', return_value=obj):
            view = JobTemplateSurveySpec()
            response = view.get(mocker.MagicMock())
            assert response == mock_response_new
            # which there was a better way to do this!
            assert response.call_args[0][1]['spec'][0]['default'] == '$encrypted$'
