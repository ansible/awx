import pytest
import requests
from unittest import mock
from awx.api.views.analytics import AnalyticsGenericView, MissingSettings, AUTOMATION_ANALYTICS_API_URL_PATH, ERROR_MISSING_USER, ERROR_MISSING_PASSWORD
from django.test.utils import override_settings
from django.test import RequestFactory
from rest_framework import status

from awx.main.utils import get_awx_version
from django.utils import translation


class TestAnalyticsGenericView:
    @pytest.mark.parametrize(
        "existing_headers,expected_headers",
        [
            ({}, {}),
            ({'Hey': 'There'}, {}),  # We don't forward just any headers
            ({'Content-Type': 'text/html', 'Content-Length': '12'}, {'Content-Type': 'text/html', 'Content-Length': '12'}),
            # Requests will auto-add the following headers (so we don't need to test them): 'Accept-Encoding', 'User-Agent', 'Accept'
        ],
    )
    def test__request_headers(self, existing_headers, expected_headers):
        expected_headers['X-Rh-Analytics-Source'] = 'controller'
        expected_headers['X-Rh-Analytics-Source-Version'] = get_awx_version()
        expected_headers['Accept-Language'] = translation.get_language()

        request = requests.session()
        request.headers.update(existing_headers)
        assert set(expected_headers.items()).issubset(set(AnalyticsGenericView._request_headers(request).items()))

    @pytest.mark.parametrize(
        "path,expected_path",
        [
            ('A/B', f'{AUTOMATION_ANALYTICS_API_URL_PATH}/A/B'),
            ('B', f'{AUTOMATION_ANALYTICS_API_URL_PATH}/B'),
            ('/a/b/c/analytics/reports/my_slug', f'{AUTOMATION_ANALYTICS_API_URL_PATH}/reports/my_slug'),
            ('/a/b/c/analytics/', f'{AUTOMATION_ANALYTICS_API_URL_PATH}/'),
            ('/a/b/c/analytics', f'{AUTOMATION_ANALYTICS_API_URL_PATH}//a/b/c/analytics'),  # Because there is no ending / on analytics we get a weird condition
            ('/a/b/c/analytics/', f'{AUTOMATION_ANALYTICS_API_URL_PATH}/'),
        ],
    )
    @pytest.mark.django_db
    def test__get_analytics_path(self, path, expected_path):
        assert AnalyticsGenericView._get_analytics_path(path) == expected_path

    @pytest.mark.django_db
    def test__get_analytics_url_no_url(self):
        with override_settings(AUTOMATION_ANALYTICS_URL=None):
            with pytest.raises(MissingSettings):
                agw = AnalyticsGenericView()
                agw._get_analytics_url('A')

    @pytest.mark.parametrize(
        "request_path,ending_url",
        [
            ('A', 'A'),
            ('A/B', 'A/B'),
            ('A/B/analytics/', ''),  # we split on analytics but because there is nothing after
            ('A/B/analytics/report', 'report'),
            ('A/B/analytics/report/slug', 'report/slug'),
        ],
    )
    @pytest.mark.django_db
    def test__get_analytics_url(self, request_path, ending_url):
        base_url = 'http://testing'
        with override_settings(AUTOMATION_ANALYTICS_URL=base_url):
            agw = AnalyticsGenericView()
            assert agw._get_analytics_url(request_path) == f'{base_url}{AUTOMATION_ANALYTICS_API_URL_PATH}/{ending_url}'

    @pytest.mark.parametrize(
        "setting_name,setting_value,raises",
        [
            ('INSIGHTS_TRACKING_STATE', None, True),
            ('INSIGHTS_TRACKING_STATE', False, True),
            ('INSIGHTS_TRACKING_STATE', True, False),
            ('INSIGHTS_TRACKING_STATE', 'Steve', False),
            ('INSIGHTS_TRACKING_STATE', 1, False),
            ('INSIGHTS_TRACKING_STATE', '', True),
        ],
    )
    @pytest.mark.django_db
    def test__get_setting(self, setting_name, setting_value, raises):
        with override_settings(**{setting_name: setting_value}):
            if raises:
                with pytest.raises(MissingSettings):
                    AnalyticsGenericView._get_setting(setting_name, False, None)
            else:
                assert AnalyticsGenericView._get_setting(setting_name, False, None) == setting_value

    @pytest.mark.parametrize(
        "settings_map, expected_auth, expected_error_keyword",
        [
            # Test case 1: Valid Red Hat credentials
            (
                {
                    'INSIGHTS_TRACKING_STATE': True,
                    'REDHAT_USERNAME': 'redhat_user',
                    'REDHAT_PASSWORD': 'redhat_pass',  # NOSONAR
                    'SUBSCRIPTIONS_USERNAME': '',
                    'SUBSCRIPTIONS_PASSWORD': '',
                },
                ('redhat_user', 'redhat_pass'),
                None,
            ),
            # Test case 2: Valid Subscription credentials
            (
                {
                    'INSIGHTS_TRACKING_STATE': True,
                    'REDHAT_USERNAME': '',
                    'REDHAT_PASSWORD': '',
                    'SUBSCRIPTIONS_USERNAME': 'subs_user',
                    'SUBSCRIPTIONS_PASSWORD': 'subs_pass',  # NOSONAR
                },
                ('subs_user', 'subs_pass'),
                None,
            ),
            # Test case 3: No credentials
            (
                {
                    'INSIGHTS_TRACKING_STATE': True,
                    'REDHAT_USERNAME': '',
                    'REDHAT_PASSWORD': '',
                    'SUBSCRIPTIONS_USERNAME': '',
                    'SUBSCRIPTIONS_PASSWORD': '',
                },
                None,
                ERROR_MISSING_USER,
            ),
            # Test case 4: Both credentials
            (
                {
                    'INSIGHTS_TRACKING_STATE': True,
                    'REDHAT_USERNAME': 'redhat_user',
                    'REDHAT_PASSWORD': 'redhat_pass',  # NOSONAR
                    'SUBSCRIPTIONS_USERNAME': 'subs_user',
                    'SUBSCRIPTIONS_PASSWORD': 'subs_pass',  # NOSONAR
                },
                ('redhat_user', 'redhat_pass'),
                None,
            ),
            # Test case 5: Missing password
            (
                {
                    'INSIGHTS_TRACKING_STATE': True,
                    'REDHAT_USERNAME': '',
                    'REDHAT_PASSWORD': '',
                    'SUBSCRIPTIONS_USERNAME': 'subs_user',  # NOSONAR
                    'SUBSCRIPTIONS_PASSWORD': '',
                },
                None,
                ERROR_MISSING_PASSWORD,
            ),
        ],
    )
    @pytest.mark.django_db
    def test__send_to_analytics_credentials(self, settings_map, expected_auth, expected_error_keyword):
        with override_settings(**settings_map):
            request = RequestFactory().post('/some/path')
            view = AnalyticsGenericView()

            if expected_auth:
                with mock.patch('requests.request') as mock_request:
                    mock_request.return_value = mock.Mock(status_code=200)

                    analytic_url = view._get_analytics_url(request.path)
                    response = view._send_to_analytics(request, 'POST')

                    # Assertions
                    mock_request.assert_called_once_with(
                        'POST',
                        analytic_url,
                        auth=expected_auth,
                        verify=mock.ANY,
                        headers=mock.ANY,
                        json=mock.ANY,
                        params=mock.ANY,
                        timeout=mock.ANY,
                    )
                    assert response.status_code == 200
            else:
                # Test when settings are missing and MissingSettings is raised
                response = view._send_to_analytics(request, 'POST')

                # # Assert that _error_response is called when MissingSettings is raised
                # mock_error_response.assert_called_once_with(expected_error_keyword, remote=False)
                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert response.data['error']['keyword'] == expected_error_keyword
