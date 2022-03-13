# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.response import Response

# AWX
# from awx.main.analytics import collectors
import awx.main.analytics.subsystem_metrics as s_metrics
from awx.main.analytics.metrics import metrics
from awx.api import renderers

from rest_framework.views import APIView


logger = logging.getLogger('awx.analytics')


class MetricsView(APIView):

    authentication_classes = []  # disables authentication
    permission_classes = []  # disables permission

    name = _('Metrics')
    swagger_topic = 'Metrics'

    renderer_classes = [renderers.PlainTextRenderer, renderers.PrometheusJSONRenderer, renderers.BrowsableAPIRenderer]

    def get(self, request):
        '''Show Metrics Details'''
        metrics_to_show = ''
        if not request.query_params.get('subsystemonly', "0") == "1":
            metrics_to_show += metrics().decode('UTF-8')
        if not request.query_params.get('dbonly', "0") == "1":
            metrics_to_show += s_metrics.metrics(request)
        return Response(metrics_to_show)
