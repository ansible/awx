# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


# Django REST Framework
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

# AWX
from awx.api.versioning import get_request_version
from awx.api.generics import (
    SubListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
    SubListCreateAttachDetachAPIView,
    SubListAPIView,
    AdHocCommandList,
)
from awx.api.base import (
    BaseVariableData,
    BaseJobHostSummariesList,
    BaseJobEventsList,
)
from awx.api.serializers import (
    GroupVariableDataSerializer,
    GroupSerializer,
    HostSerializer,
    InventorySourceSerializer,
    ActivityStreamSerializer,
)
from awx.api.views.mixins import (
    ActivityStreamEnforcementMixin,
    ControlledByScmMixin,
    EnforceParentRelationshipMixin,
)
from awx.main.models import (
    ActivityStream,
    Group,
    Host,
    InventorySource,
)


class GroupList(ListCreateAPIView):

    model = Group
    serializer_class = GroupSerializer
    capabilities_prefetch = ['inventory.admin', 'inventory.adhoc']


class GroupChildrenList(ControlledByScmMixin, EnforceParentRelationshipMixin, SubListCreateAttachDetachAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Group
    relationship = 'children'
    enforce_parent_relationship = 'inventory'

    def unattach(self, request, *args, **kwargs):
        sub_id = request.data.get('id', None)
        if sub_id is not None:
            return super(GroupChildrenList, self).unattach(request, *args, **kwargs)
        parent = self.get_parent_object()
        if not request.user.can_access(self.model, 'delete', parent):
            raise PermissionDenied()
        parent.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def is_valid_relation(self, parent, sub, created=False):
        # Prevent any cyclical group associations.
        parent_pks = set(parent.all_parents.values_list('pk', flat=True))
        parent_pks.add(parent.pk)
        child_pks = set(sub.all_children.values_list('pk', flat=True))
        child_pks.add(sub.pk)
        if parent_pks & child_pks:
            return {'error': _('Cyclical Group association.')}
        return None


class GroupPotentialChildrenList(SubListAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Group
    new_in_14 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        qs = qs.filter(inventory__pk=parent.inventory.pk)
        except_pks = set([parent.pk])
        except_pks.update(parent.all_parents.values_list('pk', flat=True))
        except_pks.update(parent.all_children.values_list('pk', flat=True))
        return qs.exclude(pk__in=except_pks)


class GroupHostsList(ControlledByScmMixin, SubListCreateAttachDetachAPIView):
    ''' the list of hosts directly below a group '''

    model = Host
    serializer_class = HostSerializer
    parent_model = Group
    relationship = 'hosts'
    capabilities_prefetch = ['inventory.admin']

    def update_raw_data(self, data):
        data.pop('inventory', None)
        return super(GroupHostsList, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        parent_group = Group.objects.get(id=self.kwargs['pk'])
        # Inject parent group inventory ID into new host data.
        request.data['inventory'] = parent_group.inventory_id
        existing_hosts = Host.objects.filter(inventory=parent_group.inventory, name=request.data.get('name', ''))
        if existing_hosts.count() > 0 and ('variables' not in request.data or
                                           request.data['variables'] == '' or
                                           request.data['variables'] == '{}' or
                                           request.data['variables'] == '---'):
            request.data['id'] = existing_hosts[0].id
            return self.attach(request, *args, **kwargs)
        return super(GroupHostsList, self).create(request, *args, **kwargs)


class GroupAllHostsList(SubListAPIView):
    ''' the list of all hosts below a group, even including subgroups '''

    model = Host
    serializer_class = HostSerializer
    parent_model = Group
    relationship = 'hosts'
    capabilities_prefetch = ['inventory.admin']

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model).distinct() # need distinct for '&' operator
        sublist_qs = parent.all_hosts.distinct()
        return qs & sublist_qs


class GroupInventorySourcesList(SubListAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    parent_model = Group
    relationship = 'inventory_sources'
    new_in_148 = True


class GroupActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Group
    relationship = 'activitystream_set'
    new_in_145 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(group=parent) | Q(host__in=parent.hosts.all()))


class GroupDetail(ControlledByScmMixin, RetrieveUpdateDestroyAPIView):

    model = Group
    serializer_class = GroupSerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        if get_request_version(request) == 1:  # TODO: deletion of automatic inventory_source, remove in 3.3
            try:
                obj.deprecated_inventory_source.delete()
            except Group.deprecated_inventory_source.RelatedObjectDoesNotExist:
                pass
        obj.delete_recursive()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupVariableData(BaseVariableData):

    model = Group
    serializer_class = GroupVariableDataSerializer


class GroupJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Group


class GroupJobEventsList(BaseJobEventsList):

    parent_model = Group


class GroupAdHocCommandsList(AdHocCommandList, SubListCreateAPIView):

    parent_model = Group
    relationship = 'ad_hoc_commands'
