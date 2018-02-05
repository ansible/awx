# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

# Django REST Framework
from rest_framework.exceptions import PermissionDenied

# AWX
from awx.api.filters import V1CredentialFilterBackend
from awx.api.generics import (
    ListCreateAPIView,
    SubListAPIView,
    RetrieveUpdateDestroyAPIView,
    ResourceAccessList,
)
from awx.main.models import (
    ActivityStream,
    Credential,
    User,
    Team,
    Role,
)
from awx.api.serializers import (
    ActivityStreamSerializer,
    CredentialSerializer,
    CredentialSerializerCreate,
    UserSerializer,
    TeamSerializer,
    RoleSerializer,
)
from awx.api.mixins import (
    CredentialViewMixin,
    ActivityStreamEnforcementMixin,
)

logger = logging.getLogger('awx.api.views')


class CredentialList(CredentialViewMixin, ListCreateAPIView):

    model = Credential
    serializer_class = CredentialSerializerCreate
    capabilities_prefetch = ['admin', 'use']
    filter_backends = ListCreateAPIView.filter_backends + [V1CredentialFilterBackend]


class CredentialOwnerUsersList(SubListAPIView):

    model = User
    serializer_class = UserSerializer
    parent_model = Credential
    relationship = 'admin_role.members'
    new_in_300 = True


class CredentialOwnerTeamsList(SubListAPIView):

    model = Team
    serializer_class = TeamSerializer
    parent_model = Credential
    new_in_300 = True

    def get_queryset(self):
        credential = get_object_or_404(self.parent_model, pk=self.kwargs['pk'])
        if not self.request.user.can_access(Credential, 'read', credential):
            raise PermissionDenied()

        content_type = ContentType.objects.get_for_model(self.model)
        teams = [c.content_object.pk for c in credential.admin_role.parents.filter(content_type=content_type)]

        return self.model.objects.filter(pk__in=teams)


class CredentialDetail(RetrieveUpdateDestroyAPIView):

    model = Credential
    serializer_class = CredentialSerializer
    filter_backends = RetrieveUpdateDestroyAPIView.filter_backends + [V1CredentialFilterBackend]


class CredentialActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Credential
    relationship = 'activitystream_set'
    new_in_145 = True


class CredentialAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = Credential
    new_in_300 = True


class CredentialObjectRolesList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Credential
    new_in_300 = True

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)
