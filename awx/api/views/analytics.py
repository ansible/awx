import requests
import logging
import urllib.parse as urlparse

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import translation

from awx.api.generics import APIView, Response
from awx.api.permissions import AnalyticsPermission
from awx.api.versioning import reverse
from awx.main.utils import get_awx_version
from rest_framework import status

from collections import OrderedDict

AUTOMATION_ANALYTICS_API_URL_PATH = "/api/tower-analytics/v1"
AWX_ANALYTICS_API_PREFIX = 'analytics'

ERROR_UPLOAD_NOT_ENABLED = "analytics-upload-not-enabled"
ERROR_MISSING_URL = "missing-url"
ERROR_MISSING_USER = "missing-user"
ERROR_MISSING_PASSWORD = "missing-password"
ERROR_NO_DATA_OR_ENTITLEMENT = "no-data-or-entitlement"
ERROR_NOT_FOUND = "not-found"
ERROR_UNAUTHORIZED = "unauthorized"
ERROR_UNKNOWN = "unknown"
ERROR_UNSUPPORTED_METHOD = "unsupported-method"

logger = logging.getLogger('awx.api.views.analytics')


class MissingSettings(Exception):
    """Settings are not correct Exception"""

    pass


class GetNotAllowedMixin(object):
    def get(self, request, format=None):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class AnalyticsRootView(APIView):
    permission_classes = (AnalyticsPermission,)
    name = _('Automation Analytics')
    swagger_topic = 'Automation Analytics'

    def get(self, request, format=None):
        data = OrderedDict()
        data['authorized'] = reverse('api:analytics_authorized')
        data['reports'] = reverse('api:analytics_reports_list')
        data['report_options'] = reverse('api:analytics_report_options_list')
        data['adoption_rate'] = reverse('api:analytics_adoption_rate')
        data['adoption_rate_options'] = reverse('api:analytics_adoption_rate_options')
        data['event_explorer'] = reverse('api:analytics_event_explorer')
        data['event_explorer_options'] = reverse('api:analytics_event_explorer_options')
        data['host_explorer'] = reverse('api:analytics_host_explorer')
        data['host_explorer_options'] = reverse('api:analytics_host_explorer_options')
        data['job_explorer'] = reverse('api:analytics_job_explorer')
        data['job_explorer_options'] = reverse('api:analytics_job_explorer_options')
        data['probe_templates'] = reverse('api:analytics_probe_templates_explorer')
        data['probe_templates_options'] = reverse('api:analytics_probe_templates_options')
        data['probe_template_for_hosts'] = reverse('api:analytics_probe_template_for_hosts_explorer')
        data['probe_template_for_hosts_options'] = reverse('api:analytics_probe_template_for_hosts_options')
        data['roi_templates'] = reverse('api:analytics_roi_templates_explorer')
        data['roi_templates_options'] = reverse('api:analytics_roi_templates_options')
        return Response(data)


class AnalyticsGenericView(APIView):
    """
    Example:
        headers = {
            'Content-Type': 'application/json',
        }

        params = {
            'limit': '20',
            'offset': '0',
            'sort_by': 'name:asc',
        }

        json_data = {
            'limit': '20',
            'offset': '0',
            'sort_options': 'name',
            'sort_order': 'asc',
            'tags': [],
            'slug': [],
            'name': [],
            'description': '',
        }

        response = requests.post(f'{AUTOMATION_ANALYTICS_API_URL}/reports/', params=params,
                                 headers=headers, json=json_data)

        return Response(response.json(), status=response.status_code)
    """

    permission_classes = (AnalyticsPermission,)

    @staticmethod
    def _request_headers(request):
        headers = {}
        for header in ['Content-Type', 'Content-Length', 'Accept-Encoding', 'User-Agent', 'Accept']:
            if request.headers.get(header, None):
                headers[header] = request.headers.get(header)
        headers['X-Rh-Analytics-Source'] = 'controller'
        headers['X-Rh-Analytics-Source-Version'] = get_awx_version()
        headers['Accept-Language'] = translation.get_language()

        return headers

    @staticmethod
    def _get_analytics_path(request_path):
        parts = request_path.split(f'{AWX_ANALYTICS_API_PREFIX}/')
        path_specific = parts[-1]
        return f"{AUTOMATION_ANALYTICS_API_URL_PATH}/{path_specific}"

    def _get_analytics_url(self, request_path):
        analytics_path = self._get_analytics_path(request_path)
        url = getattr(settings, 'AUTOMATION_ANALYTICS_URL', None)
        if not url:
            raise MissingSettings(ERROR_MISSING_URL)
        url_parts = urlparse.urlsplit(url)
        analytics_url = urlparse.urlunsplit([url_parts.scheme, url_parts.netloc, analytics_path, url_parts.query, url_parts.fragment])
        return analytics_url

    @staticmethod
    def _get_setting(setting_name, default, error_message):
        setting = getattr(settings, setting_name, default)
        if not setting:
            raise MissingSettings(error_message)
        return setting

    @staticmethod
    def _error_response(keyword, message=None, remote=True, remote_status_code=None, status_code=status.HTTP_403_FORBIDDEN):
        text = {"error": {"remote": remote, "remote_status": remote_status_code, "keyword": keyword}}
        if message:
            text["error"]["message"] = message
        return Response(text, status=status_code)

    def _error_response_404(self, response):
        try:
            json_response = response.json()
            # Subscription/entitlement problem or missing tenant data in AA db => HTTP 403
            message = json_response.get('error', None)
            if message:
                return self._error_response(ERROR_NO_DATA_OR_ENTITLEMENT, message, remote=True, remote_status_code=response.status_code)

            # Standard 404 problem => HTTP 404
            message = json_response.get('detail', None) or response.text
        except requests.exceptions.JSONDecodeError:
            # Unexpected text => still HTTP 404
            message = response.text

        return self._error_response(ERROR_NOT_FOUND, message, remote=True, remote_status_code=status.HTTP_404_NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def _update_response_links(json_response):
        if not json_response.get('links', None):
            return

        for key, value in json_response['links'].items():
            if value:
                json_response['links'][key] = value.replace(AUTOMATION_ANALYTICS_API_URL_PATH, f"/api/v2/{AWX_ANALYTICS_API_PREFIX}")

    def _forward_response(self, response):
        try:
            content_type = response.headers.get('content-type', '')
            if content_type.find('application/json') != -1:
                json_response = response.json()
                self._update_response_links(json_response)

                return Response(json_response, status=response.status_code)
        except Exception as e:
            logger.error(f"Analytics API: Response error: {e}")

        return Response(response.content, status=response.status_code)

    def _send_to_analytics(self, request, method):
        try:
            headers = self._request_headers(request)

            self._get_setting('INSIGHTS_TRACKING_STATE', False, ERROR_UPLOAD_NOT_ENABLED)
            url = self._get_analytics_url(request.path)
            rh_user = self._get_setting('REDHAT_USERNAME', None, ERROR_MISSING_USER)
            rh_password = self._get_setting('REDHAT_PASSWORD', None, ERROR_MISSING_PASSWORD)

            if method not in ["GET", "POST", "OPTIONS"]:
                return self._error_response(ERROR_UNSUPPORTED_METHOD, method, remote=False, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                response = requests.request(
                    method,
                    url,
                    auth=(rh_user, rh_password),
                    verify=settings.INSIGHTS_CERT_PATH,
                    params=request.query_params,
                    headers=headers,
                    json=request.data,
                    timeout=(31, 31),
                )
            #
            # Missing or wrong user/pass
            #
            if response.status_code == status.HTTP_401_UNAUTHORIZED:
                text = (response.text or '').rstrip("\n")
                return self._error_response(ERROR_UNAUTHORIZED, text, remote=True, remote_status_code=response.status_code)
            #
            # Not found, No entitlement or No data in Analytics
            #
            elif response.status_code == status.HTTP_404_NOT_FOUND:
                return self._error_response_404(response)
            #
            # Success or not a 401/404 errors are just forwarded
            #
            else:
                return self._forward_response(response)

        except MissingSettings as e:
            logger.warning(f"Analytics API: Setting missing: {e.args[0]}")
            return self._error_response(e.args[0], remote=False)
        except requests.exceptions.RequestException as e:
            logger.error(f"Analytics API: Request error: {e}")
            return self._error_response(ERROR_UNKNOWN, str(e), remote=False, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Analytics API: Error: {e}")
            return self._error_response(ERROR_UNKNOWN, str(e), remote=False, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalyticsGenericListView(AnalyticsGenericView):
    def get(self, request, format=None):
        return self._send_to_analytics(request, method="GET")

    def post(self, request, format=None):
        return self._send_to_analytics(request, method="POST")

    def options(self, request, format=None):
        return self._send_to_analytics(request, method="OPTIONS")


class AnalyticsGenericDetailView(AnalyticsGenericView):
    def get(self, request, slug, format=None):
        return self._send_to_analytics(request, method="GET")

    def post(self, request, slug, format=None):
        return self._send_to_analytics(request, method="POST")

    def options(self, request, slug, format=None):
        return self._send_to_analytics(request, method="OPTIONS")


class AnalyticsAuthorizedView(AnalyticsGenericListView):
    name = _("Authorized")


class AnalyticsReportsList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("Reports")
    swagger_topic = "Automation Analytics"


class AnalyticsReportDetail(AnalyticsGenericDetailView):
    name = _("Report")


class AnalyticsReportOptionsList(AnalyticsGenericListView):
    name = _("Report Options")


class AnalyticsAdoptionRateList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("Adoption Rate")


class AnalyticsEventExplorerList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("Event Explorer")


class AnalyticsHostExplorerList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("Host Explorer")


class AnalyticsJobExplorerList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("Job Explorer")


class AnalyticsProbeTemplatesList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("Probe Templates")


class AnalyticsProbeTemplateForHostsList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("Probe Template For Hosts")


class AnalyticsRoiTemplatesList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("ROI Templates")
