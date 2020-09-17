# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied


# AWX
# from awx.main.analytics import collectors
from awx.main.analytics.metrics import metrics
from awx.api import renderers

from awx.api.generics import (
    APIView,
)


logger = logging.getLogger('awx.analytics')


class MetricsView(APIView):

    name = _('Metrics')
    swagger_topic = 'Metrics'

    renderer_classes = [renderers.PlainTextRenderer,
                        renderers.PrometheusJSONRenderer,
                        renderers.BrowsableAPIRenderer,]

    def get(self, request):
        ''' Show Metrics Details '''
        if (request.user.is_superuser or request.user.is_system_auditor):
            return Response(metrics().decode('UTF-8'))
        raise PermissionDenied()

