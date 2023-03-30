import pytest
import requests
from awx.api.views.analytics import AnalyticsGenericView, MissingSettings, AUTOMATION_ANALYTICS_API_URL_PATH
from django.test.utils import override_settings

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
