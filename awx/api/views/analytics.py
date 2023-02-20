import requests
import logging

from django.utils.translation import gettext_lazy as _

from awx.api.generics import APIView, Response
from awx.api.permissions import IsSystemAdminOrAuditor
from awx.api.versioning import reverse
from rest_framework.permissions import AllowAny
from rest_framework import status

from collections import OrderedDict

# docker-docker API request requires:
# ```
# docker network connect koku_default tools_awx_1
# ```
AUTOMATION_ANALYTICS_API_URL = "http://automation-analytics-backend_fastapi_1:8080/api/tower-analytics/v1"
# AUTOMATION_ANALYTICS_API_URL = "http://localhost:8004/api/tower-analytics/v1"

logger = logging.getLogger('awx.api.views')


class GetNotAllowedMixin(object):
    def get(self, request, format=None):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class AnalyticsRootView(APIView):
    permission_classes = (AllowAny,)
    name = _('Automation Analytics')
    swagger_topic = 'Automation Analytics'

    def get(self, request, format=None):
        data = OrderedDict()
        data['reports'] = reverse('analytics_reports_list')
        return Response(data)


class AnalyticsTestList(APIView):
    name = _("Testing")
    permission_classes = (IsSystemAdminOrAuditor,)
    swagger_topic = "AA"

    def get(self, request, format=None):
        logger.info(f"TEST: {type(request.headers)}")
        new_headers = request.headers.copy()

        data = {
            'get': {
                'method': request.method,
                'content-type': request.content_type,
                'data': request.data,
                'query_params': request.query_params,
                'headers': new_headers,
                'path': request.path,
            }
        }
        return Response(data)

    def post(self, request, format=None):
        return self.get(request, format)


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

    permission_classes = (IsSystemAdminOrAuditor,)

    def _remove_api_path_prefix(self, request_path):
        parts = request_path.split('analytics/')
        return parts[len(parts) - 1]

    def _forward_get(self, request, format=None):
        headers = {'Content-Type': 'application/json'}
        analytics_path = self._remove_api_path_prefix(request.path)
        response = requests.get(f'{AUTOMATION_ANALYTICS_API_URL}/{analytics_path}', params=request.query_params, headers=headers)
        return Response(response.json(), status=response.status_code)

    def _forward_post(self, request, format=None):
        analytics_path = self._remove_api_path_prefix(request.path)
        response = requests.post(f'{AUTOMATION_ANALYTICS_API_URL}/{analytics_path}', params=request.query_params, headers=request.headers, json=request.data)
        return Response(response.json(), status=response.status_code)


class AnalyticsGenericListView(AnalyticsGenericView):
    def get(self, request, format=None):
        return self._forward_get(request, format)

    def post(self, request, format=None):
        return self._forward_post(request, format)


class AnalyticsGenericDetailView(AnalyticsGenericView):
    def get(self, request, slug, format=None):
        return self._forward_get(request, format)

    def post(self, request, slug, format=None):
        return self._forward_post(request, format)


class AnalyticsAuthorizedView(AnalyticsGenericListView):
    name = _("Authorized")


class AnalyticsReportsList(AnalyticsGenericListView):
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
    """TODO: Allow Http GET?"""

    name = _("Job Explorer")


class AnalyticsProbeTemplatesList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("Probe Templates")


class AnalyticsProbeTemplateForHostsList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("Probe Template For Hosts")


class AnalyticsRoiTemplatesList(GetNotAllowedMixin, AnalyticsGenericListView):
    name = _("ROI Templates")
