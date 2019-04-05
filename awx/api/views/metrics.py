# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now

# Django REST Framework
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, StaticHTMLRenderer

# AWX
# from awx.main.analytics import collectors
from awx.main.analytics.metrics import metrics
from awx.api import renderers

from awx.api.generics import (
    APIView,
)

from awx.api.serializers import (
    InventorySerializer,
    ActivityStreamSerializer,
)

logger = logging.getLogger('awx.main.analytics')



class MetricsView(APIView):

    view_name = _('Metrics')
    swagger_topic = 'Metrics'

    renderer_classes = [renderers.PlainTextRenderer,
                        renderers.BrowsableAPIRenderer,
                        JSONRenderer,]

    def get(self, request, format='txt'):
        ''' Show Metrics Details '''
        return Response(metrics().decode('UTF-8'))
