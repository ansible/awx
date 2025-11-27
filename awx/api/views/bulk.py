from collections import OrderedDict

from ansible_base.lib.utils.schema import extend_schema_if_available

from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.response import Response

from awx.main.models import UnifiedJob, Host
from awx.api.generics import (
    GenericAPIView,
    APIView,
)
from awx.api import (
    serializers,
    renderers,
)


@extend_schema_if_available(extensions={"x-ai-description": "Retrieves a list of available bulk actions"})
class BulkView(APIView):
    name = _('Bulk')
    swagger_topic = 'Bulk'

    permission_classes = [IsAuthenticated]
    renderer_classes = [
        renderers.BrowsableAPIRenderer,
        JSONRenderer,
    ]
    allowed_methods = ['GET', 'OPTIONS']

    def get(self, request, format=None):
        '''List top level resources'''
        data = OrderedDict()
        data['host_create'] = reverse('api:bulk_host_create', request=request)
        data['host_delete'] = reverse('api:bulk_host_delete', request=request)
        data['job_launch'] = reverse('api:bulk_job_launch', request=request)
        return Response(data)


@extend_schema_if_available(extensions={"x-ai-description": "Bulk launch job templates"})
class BulkJobLaunchView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    model = UnifiedJob
    serializer_class = serializers.BulkJobLaunchSerializer
    allowed_methods = ['GET', 'POST', 'OPTIONS']

    def get(self, request):
        data = OrderedDict()
        data['detail'] = "Specify a list of unified job templates to launch alongside their launchtime parameters"
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        bulkjob_serializer = serializers.BulkJobLaunchSerializer(data=request.data, context={'request': request})
        if bulkjob_serializer.is_valid():
            result = bulkjob_serializer.create(bulkjob_serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(bulkjob_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_if_available(extensions={"x-ai-description": "Bulk create hosts"})
class BulkHostCreateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    model = Host
    serializer_class = serializers.BulkHostCreateSerializer
    allowed_methods = ['GET', 'POST', 'OPTIONS']

    def get(self, request):
        return Response({"detail": "Bulk create hosts with this endpoint"}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = serializers.BulkHostCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.create(serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_if_available(extensions={"x-ai-description": "Bulk delete hosts"})
class BulkHostDeleteView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    model = Host
    serializer_class = serializers.BulkHostDeleteSerializer
    allowed_methods = ['GET', 'POST', 'OPTIONS']

    def get(self, request):
        return Response({"detail": "Bulk delete hosts with this endpoint"}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = serializers.BulkHostDeleteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.delete(serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
