# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.conf import settings
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

# Django REST Framework
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers

# AWX
from awx.main.models import ActivityStream, Inventory, JobTemplate, Role, User, InstanceGroup, InventoryUpdateEvent, InventoryUpdate

from ansible_base.lib.utils.schema import extend_schema_if_available

from awx.api.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    SubListAPIView,
    SubListAttachDetachAPIView,
    ResourceAccessList,
    CopyAPIView,
)
from awx.api.views.labels import LabelSubListCreateAttachDetachView


from awx.api.serializers import (
    InventorySerializer,
    ConstructedInventorySerializer,
    ActivityStreamSerializer,
    RoleSerializer,
    InstanceGroupSerializer,
    InventoryUpdateEventSerializer,
    JobTemplateSerializer,
)
from awx.api.views.mixin import RelatedJobsPreventDeleteMixin

from awx.api.pagination import UnifiedJobEventPagination


logger = logging.getLogger('awx.api.views.organization')


class InventoryUpdateEventsList(SubListAPIView):
    model = InventoryUpdateEvent
    serializer_class = InventoryUpdateEventSerializer
    parent_model = InventoryUpdate
    relationship = 'inventory_update_events'
    name = _('Inventory Update Events List')
    search_fields = ('stdout',)
    pagination_class = UnifiedJobEventPagination
    resource_purpose = 'events of an inventory update'

    def get_queryset(self):
        iu = self.get_parent_object()
        self.check_parent_access(iu)
        return iu.get_event_queryset()

    def finalize_response(self, request, response, *args, **kwargs):
        response['X-UI-Max-Events'] = settings.MAX_UI_JOB_EVENTS
        return super(InventoryUpdateEventsList, self).finalize_response(request, response, *args, **kwargs)


class InventoryList(ListCreateAPIView):
    model = Inventory
    serializer_class = InventorySerializer
    resource_purpose = 'inventories'


class InventoryDetail(RelatedJobsPreventDeleteMixin, RetrieveUpdateDestroyAPIView):
    model = Inventory
    serializer_class = InventorySerializer
    resource_purpose = 'inventory detail'

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        kind = self.request.data.get('kind') or kwargs.get('kind')

        # Do not allow changes to an Inventory kind.
        if kind is not None and obj.kind != kind:
            return Response(
                dict(error=_('You cannot turn a regular inventory into a "smart" or "constructed" inventory.')), status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
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


class ConstructedInventoryDetail(InventoryDetail):
    serializer_class = ConstructedInventorySerializer
    resource_purpose = 'constructed inventory detail'


class ConstructedInventoryList(InventoryList):
    serializer_class = ConstructedInventorySerializer
    resource_purpose = 'constructed inventories'

    def get_queryset(self):
        r = super().get_queryset()
        return r.filter(kind='constructed')


@extend_schema_if_available(extensions={"x-ai-description": "Get or create input inventory inventory"})
class InventoryInputInventoriesList(SubListAttachDetachAPIView):
    model = Inventory
    serializer_class = InventorySerializer
    parent_model = Inventory
    relationship = 'input_inventories'
    resource_purpose = 'input inventories of a constructed inventory'

    def is_valid_relation(self, parent, sub, created=False):
        if sub.kind == 'constructed':
            raise serializers.ValidationError({'error': 'You cannot add a constructed inventory to another constructed inventory.'})


@extend_schema_if_available(extensions={"x-ai-description": "Get activity stream for an inventory"})
class InventoryActivityStreamList(SubListAPIView):
    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Inventory
    relationship = 'activitystream_set'
    search_fields = ('changes',)
    resource_purpose = 'activity stream for an inventory'

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
    resource_purpose = 'instance groups of an inventory'


class InventoryAccessList(ResourceAccessList):
    model = User  # needs to be User for AccessLists's
    parent_model = Inventory
    resource_purpose = 'users who can access the inventory'


class InventoryObjectRolesList(SubListAPIView):
    model = Role
    serializer_class = RoleSerializer
    parent_model = Inventory
    search_fields = ('role_field', 'content_type__model')
    deprecated = True
    resource_purpose = 'roles of an inventory'

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class InventoryJobTemplateList(SubListAPIView):
    model = JobTemplate
    serializer_class = JobTemplateSerializer
    parent_model = Inventory
    relationship = 'jobtemplates'
    resource_purpose = 'job templates using an inventory'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(inventory=parent)


class InventoryLabelList(LabelSubListCreateAttachDetachView):
    parent_model = Inventory
    resource_purpose = 'labels of an inventory'


class InventoryCopy(CopyAPIView):
    model = Inventory
    copy_return_serializer_class = InventorySerializer
    resource_purpose = 'copy of an inventory'
