# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.utils.translation import gettext_lazy as _

# Django REST Framework
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied


# AWX
# from awx.main.analytics import collectors
import awx.main.analytics.subsystem_metrics as s_metrics
from awx.main.analytics.metrics import metrics
from awx.api import renderers

from awx.api.generics import APIView


logger = logging.getLogger('awx.analytics')


class MetricsView(APIView):

    name = _('Metrics')
    swagger_topic = 'Metrics'

    renderer_classes = [renderers.PlainTextRenderer, renderers.PrometheusJSONRenderer, renderers.BrowsableAPIRenderer]

    def get(self, request):
        '''Show Metrics Details'''
        if request.user.is_superuser or request.user.is_system_auditor:
            metrics_to_show = ''
            if not request.query_params.get('subsystemonly', "0") == "1":
                metrics_to_show += metrics().decode('UTF-8')
            if not request.query_params.get('dbonly', "0") == "1":
                metrics_to_show += s_metrics.metrics(request)
            return Response(metrics_to_show)
        raise PermissionDenied()
