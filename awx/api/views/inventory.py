# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.conf import settings
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

# AWX
from awx.main.models import (
    ActivityStream,
    Inventory,
    JobTemplate,
    Role,
    User,
    InstanceGroup,
    InventoryUpdateEvent,
    InventoryUpdate,
    InventorySource,
    CustomInventoryScript,
)
from awx.api.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    SubListAPIView,
    SubListAttachDetachAPIView,
    ResourceAccessList,
    CopyAPIView,
)

from awx.api.serializers import (
    InventorySerializer,
    ActivityStreamSerializer,
    RoleSerializer,
    InstanceGroupSerializer,
    InventoryUpdateEventSerializer,
    CustomInventoryScriptSerializer,
    JobTemplateSerializer,
)
from awx.api.views.mixin import (
    RelatedJobsPreventDeleteMixin,
    ControlledByScmMixin,
)

logger = logging.getLogger('awx.api.views.organization')


class InventoryUpdateEventsList(SubListAPIView):

    model = InventoryUpdateEvent
    serializer_class = InventoryUpdateEventSerializer
    parent_model = InventoryUpdate
    relationship = 'inventory_update_events'
    name = _('Inventory Update Events List')
    search_fields = ('stdout',)

    def finalize_response(self, request, response, *args, **kwargs):
        response['X-UI-Max-Events'] = settings.MAX_UI_JOB_EVENTS
        return super(InventoryUpdateEventsList, self).finalize_response(request, response, *args, **kwargs)


class InventoryScriptList(ListCreateAPIView):

    deprecated = True

    model = CustomInventoryScript
    serializer_class = CustomInventoryScriptSerializer


class InventoryScriptDetail(RetrieveUpdateDestroyAPIView):

    deprecated = True

    model = CustomInventoryScript
    serializer_class = CustomInventoryScriptSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        can_delete = request.user.can_access(self.model, 'delete', instance)
        if not can_delete:
            raise PermissionDenied(_("Cannot delete inventory script."))
        for inv_src in InventorySource.objects.filter(source_script=instance):
            inv_src.source_script = None
            inv_src.save()
        return super(InventoryScriptDetail, self).destroy(request, *args, **kwargs)


class InventoryScriptObjectRolesList(SubListAPIView):

    deprecated = True

    model = Role
    serializer_class = RoleSerializer
    parent_model = CustomInventoryScript
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class InventoryScriptCopy(CopyAPIView):

    deprecated = True

    model = CustomInventoryScript
    copy_return_serializer_class = CustomInventoryScriptSerializer


class InventoryList(ListCreateAPIView):

    model = Inventory
    serializer_class = InventorySerializer


class InventoryDetail(RelatedJobsPreventDeleteMixin, ControlledByScmMixin, RetrieveUpdateDestroyAPIView):

    model = Inventory
    serializer_class = InventorySerializer

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        kind = self.request.data.get('kind') or kwargs.get('kind')

        # Do not allow changes to an Inventory kind.
        if kind is not None and obj.kind != kind:
            return Response(dict(error=_('You cannot turn a regular inventory into a "smart" inventory.')),
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super(InventoryDetail, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        self.check_related_active_jobs(obj)  # related jobs mixin
        try:
            obj.schedule_deletion(getattr(request.user, 'id', None))
            return Response(status=status.HTTP_202_ACCEPTED)
        except RuntimeError as e:
            return Response(dict(error=_("{0}".format(e))), status=status.HTTP_400_BAD_REQUEST)


class InventoryActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Inventory
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(inventory=parent) | Q(host__in=parent.hosts.all()) | Q(group__in=parent.groups.all()))


class InventoryInstanceGroupsList(SubListAttachDetachAPIView):

    model = InstanceGroup
    serializer_class = InstanceGroupSerializer
    parent_model = Inventory
    relationship = 'instance_groups'


class InventoryAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = Inventory


class InventoryObjectRolesList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Inventory
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class InventoryJobTemplateList(SubListAPIView):

    model = JobTemplate
    serializer_class = JobTemplateSerializer
    parent_model = Inventory
    relationship = 'jobtemplates'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(inventory=parent)


class InventoryCopy(CopyAPIView):

    model = Inventory
    copy_return_serializer_class = InventorySerializer
