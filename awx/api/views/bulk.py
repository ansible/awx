from collections import OrderedDict

from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.response import Response

from awx.api.generics import (
    GenericAPIView,
    APIView,
)
from awx.api import (
    serializers,
    renderers,
)


class BulkView(APIView):
    _ignore_model_permissions = True
    permission_classes = [IsAuthenticated]
    renderer_classes = [
        renderers.BrowsableAPIRenderer,
        JSONRenderer,
    ]
    allowed_methods = ['GET', 'OPTIONS']

    def get(self, request, format=None):
        '''List top level resources'''
        data = OrderedDict()
        data['bulk_host_create'] = reverse('api:bulk_host_create', request=request)
        return Response(data)


class BulkHostCreateView(GenericAPIView):
    _ignore_model_permissions = True
    permission_classes = [IsAuthenticated]
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
