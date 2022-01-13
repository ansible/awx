# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

from awx.main.models import InstanceLink, Instance
from django.utils.translation import ugettext_lazy as _

from awx.api.generics import APIView, Response

from awx.api.serializers import InstanceLinkSerializer, InstanceNodeSerializer


class MeshVisualizer(APIView):

    name = _("Mesh Visualizer")

    def get(self, request, format=None):

        data = {
            'nodes': InstanceNodeSerializer(Instance.objects.all(), many=True).data,
            'links': InstanceLinkSerializer(InstanceLink.objects.all(), many=True).data,
        }

        return Response(data)
