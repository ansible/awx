import pytest

from awx.api.views import (
    ApiV1RootView,
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

