# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

from django.utils.translation import ugettext_lazy as _

from awx.api.generics import APIView, Response
from awx.api.permissions import IsSystemAdminOrAuditor
from awx.api.serializers import InstanceLinkSerializer, InstanceNodeSerializer
from awx.main.models import InstanceLink, Instance


class MeshVisualizer(APIView):

    name = _("Mesh Visualizer")
    permission_classes = (IsSystemAdminOrAuditor,)
    swagger_topic = "System Configuration"

    def get(self, request, format=None):

        data = {
            'nodes': InstanceNodeSerializer(Instance.objects.all(), many=True).data,
            'links': InstanceLinkSerializer(InstanceLink.objects.select_related('target', 'source'), many=True).data,
        }

        return Response(data)
