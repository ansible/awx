import requests
import logging

from django.utils.translation import gettext_lazy as _

from awx.api.generics import APIView, Response
from awx.api.permissions import IsSystemAdminOrAuditor
from awx.api.versioning import reverse
from rest_framework.permissions import AllowAny

from collections import OrderedDict

# docker-docker API request requires:
# ```
# docker network connect koku_default tools_awx_1
# ```
AUTOMATION_ANALYTICS_API_URL = "http://automation-analytics-backend_fastapi_1:8080/api/tower-analytics/v1"
# AUTOMATION_ANALYTICS_API_URL = "http://localhost:8004/api/tower-analytics/v1"

logger = logging.getLogger('awx.api.views')


class AnalyticsRootView(APIView):
    permission_classes = (AllowAny,)
    name = _('Automation Analytics')
    # versioning_class = None
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

    # def post_proxy(self, url_path, request, format=None):


class AnalyticsReportsList(AnalyticsGenericView):
    name = _("Reports")
    swagger_topic = "Automation Analytics"

    def post(self, request, format=None):
        response = requests.post(f'{AUTOMATION_ANALYTICS_API_URL}/reports/', params=request.query_params, headers=request.headers, json=request.data)

        return Response(response.json(), status=response.status_code)


class AnalyticsReportOptionsList(AnalyticsGenericView):
    name = _("Report Options")

    def get(self, request, format=None):
        response = requests.get(f'{AUTOMATION_ANALYTICS_API_URL}/report_options/', params=request.query_params, headers={'Content-Type': 'application/json'})

        return Response(response.json(), status=response.status_code)
