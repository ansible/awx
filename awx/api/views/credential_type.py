# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.exceptions import PermissionDenied

# AWX
from awx.api.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    SubListAPIView,
)
from awx.api.serializers import (
    CredentialTypeSerializer,
    CredentialSerializer,
    ActivityStreamSerializer,
)
from awx.api.views.mixins import ActivityStreamEnforcementMixin
from awx.main.models import (
    ActivityStream,
    Credential,
    CredentialType,
)


logger = logging.getLogger('awx.api.views')


class CredentialTypeList(ListCreateAPIView):

    model = CredentialType
    serializer_class = CredentialTypeSerializer
    new_in_320 = True
    new_in_api_v2 = True


class CredentialTypeDetail(RetrieveUpdateDestroyAPIView):

    model = CredentialType
    serializer_class = CredentialTypeSerializer
    new_in_320 = True
    new_in_api_v2 = True

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.managed_by_tower:
            raise PermissionDenied(detail=_("Deletion not allowed for managed credential types"))
        if instance.credentials.exists():
            raise PermissionDenied(detail=_("Credential types that are in use cannot be deleted"))
        return super(CredentialTypeDetail, self).destroy(request, *args, **kwargs)


class CredentialTypeCredentialList(SubListAPIView):

    model = Credential
    parent_model = CredentialType
    relationship = 'credentials'
    serializer_class = CredentialSerializer
    new_in_320 = True
    new_in_api_v2 = True


class CredentialTypeActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = CredentialType
    relationship = 'activitystream_set'
    new_in_320 = True
    new_in_api_v2 = True
