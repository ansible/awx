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

# AWX
from awx.main.models import ActivityStream, Inventory, JobTemplate, Role, User, InstanceGroup, InventoryUpdateEvent, InventoryUpdate

from awx.main.models.label import Label

from awx.api.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    SubListAPIView,
    SubListAttachDetachAPIView,
    ResourceAccessList,
    CopyAPIView,
    DeleteLastUnattachLabelMixin,
    SubListCreateAttachDetachAPIView,
)


from awx.api.serializers import (
    InventorySerializer,
    ActivityStreamSerializer,
    RoleSerializer,
    InstanceGroupSerializer,
    InventoryUpdateEventSerializer,
    JobTemplateSerializer,
    LabelSerializer,
)
from awx.api.views.mixin import RelatedJobsPreventDeleteMixin, ControlledByScmMixin

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


class InventoryDetail(RelatedJobsPreventDeleteMixin, ControlledByScmMixin, RetrieveUpdateDestroyAPIView):

    model = Inventory
    serializer_class = InventorySerializer

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        kind = self.request.data.get('kind') or kwargs.get('kind')

        # Do not allow changes to an Inventory kind.
        if kind is not None and obj.kind != kind:
            return Response(dict(error=_('You cannot turn a regular inventory into a "smart" inventory.')), status=status.HTTP_405_METHOD_NOT_ALLOWED)
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

    model = User  # needs to be User for AccessLists's
    parent_model = Inventory


class InventoryObjectRolesList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Inventory
    search_fields = ('role_field', 'content_type__model')

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


class InventoryLabelList(DeleteLastUnattachLabelMixin, SubListCreateAttachDetachAPIView, SubListAPIView):

    model = Label
    serializer_class = LabelSerializer
    parent_model = Inventory
    relationship = 'labels'

    def post(self, request, *args, **kwargs):
        # If a label already exists in the database, attach it instead of erroring out
        # that it already exists
        if 'id' not in request.data and 'name' in request.data and 'organization' in request.data:
            existing = Label.objects.filter(name=request.data['name'], organization_id=request.data['organization'])
            if existing.exists():
                existing = existing[0]
                request.data['id'] = existing.id
                del request.data['name']
                del request.data['organization']
        if Label.objects.filter(inventory_labels=self.kwargs['pk']).count() > 100:
            return Response(
                dict(msg=_('Maximum number of labels for {} reached.'.format(self.parent_model._meta.verbose_name_raw))), status=status.HTTP_400_BAD_REQUEST
            )
        return super(InventoryLabelList, self).post(request, *args, **kwargs)


class InventoryCopy(CopyAPIView):

    model = Inventory
    copy_return_serializer_class = InventorySerializer
