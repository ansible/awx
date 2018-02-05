# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from rest_framework.response import Response
from rest_framework import status

from awx.api.generics import (
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    SubListAPIView,
    RetrieveAPIView,
    RetrieveDestroyAPIView,
)
from awx.api.base import BaseAdHocCommandEventsList
from awx.api.serializers import (
    ActivityStreamSerializer,
    AdHocCommandSerializer,
    AdHocCommandEventSerializer,
    AdHocCommandCancelSerializer,
    AdHocCommandListSerializer,
    AdHocCommandRelaunchSerializer,
    NotificationSerializer,
)
from awx.api.mixins import (
    ActivityStreamEnforcementMixin,
    UnifiedJobDeletionMixin,
)
from awx.main.models import (
    ActivityStream,
    AdHocCommand,
    AdHocCommandEvent,
    Credential,
    Group,
    Host,
    Notification,
    UnifiedJobStdout,
)
from awx.main.utils import (
    get_pk_from_dict,
    get_object_or_400,
)


class AdHocCommandList(ListCreateAPIView):

    model = AdHocCommand
    serializer_class = AdHocCommandListSerializer
    new_in_220 = True
    always_allow_superuser = False

    @csrf_exempt
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(AdHocCommandList, self).dispatch(*args, **kwargs)

    def update_raw_data(self, data):
        # Hide inventory and limit fields from raw data, since they will be set
        # automatically by sub list create view.
        parent_model = getattr(self, 'parent_model', None)
        if parent_model in (Host, Group):
            data.pop('inventory', None)
            data.pop('limit', None)
        return super(AdHocCommandList, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        # Inject inventory ID and limit if parent objects is a host/group.
        if hasattr(self, 'get_parent_object') and not getattr(self, 'parent_key', None):
            data = request.data
            # HACK: Make request data mutable.
            if getattr(data, '_mutable', None) is False:
                data._mutable = True
            parent_obj = self.get_parent_object()
            if isinstance(parent_obj, (Host, Group)):
                data['inventory'] = parent_obj.inventory_id
                data['limit'] = parent_obj.name

        # Check for passwords needed before creating ad hoc command.
        credential_pk = get_pk_from_dict(request.data, 'credential')
        if credential_pk:
            credential = get_object_or_400(Credential, pk=credential_pk)
            needed = credential.passwords_needed
            provided = dict([(field, request.data.get(field, '')) for field in needed])
            if not all(provided.values()):
                data = dict(passwords_needed_to_start=needed)
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

        response = super(AdHocCommandList, self).create(request, *args, **kwargs)
        if response.status_code != status.HTTP_201_CREATED:
            return response

        # Start ad hoc command running when created.
        ad_hoc_command = get_object_or_400(self.model, pk=response.data['id'])
        result = ad_hoc_command.signal_start(**request.data)
        if not result:
            data = dict(passwords_needed_to_start=ad_hoc_command.passwords_needed_to_start)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return response


class AdHocCommandDetail(UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = AdHocCommand
    serializer_class = AdHocCommandSerializer
    new_in_220 = True


class AdHocCommandCancel(RetrieveAPIView):

    model = AdHocCommand
    obj_permission_type = 'cancel'
    serializer_class = AdHocCommandCancelSerializer
    new_in_220 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class AdHocCommandRelaunch(GenericAPIView):

    model = AdHocCommand
    obj_permission_type = 'start'
    serializer_class = AdHocCommandRelaunchSerializer
    new_in_220 = True

    # FIXME: Figure out why OPTIONS request still shows all fields.

    @csrf_exempt
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(AdHocCommandRelaunch, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        data = dict(passwords_needed_to_start=obj.passwords_needed_to_start)
        return Response(data)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        # Re-validate ad hoc command against serializer to check if module is
        # still allowed.
        data = {}
        for field in ('job_type', 'inventory_id', 'limit', 'credential_id',
                      'module_name', 'module_args', 'forks', 'verbosity',
                      'extra_vars', 'become_enabled'):
            if field.endswith('_id'):
                data[field[:-3]] = getattr(obj, field)
            else:
                data[field] = getattr(obj, field)
        serializer = AdHocCommandSerializer(data=data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        # Check for passwords needed before copying ad hoc command.
        needed = obj.passwords_needed_to_start
        provided = dict([(field, request.data.get(field, '')) for field in needed])
        if not all(provided.values()):
            data = dict(passwords_needed_to_start=needed)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # Copy and start the new ad hoc command.
        new_ad_hoc_command = obj.copy()
        result = new_ad_hoc_command.signal_start(**request.data)
        if not result:
            data = dict(passwords_needed_to_start=new_ad_hoc_command.passwords_needed_to_start)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = AdHocCommandSerializer(new_ad_hoc_command, context=self.get_serializer_context()).data
            # Add ad_hoc_command key to match what was previously returned.
            data['ad_hoc_command'] = new_ad_hoc_command.id
            headers = {'Location': new_ad_hoc_command.get_absolute_url(request=request)}
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class AdHocCommandEventList(ListAPIView):

    model = AdHocCommandEvent
    serializer_class = AdHocCommandEventSerializer
    new_in_220 = True


class AdHocCommandEventDetail(RetrieveAPIView):

    model = AdHocCommandEvent
    serializer_class = AdHocCommandEventSerializer
    new_in_220 = True


class AdHocCommandAdHocCommandEventsList(BaseAdHocCommandEventsList):

    parent_model = AdHocCommand
    new_in_220 = True


class AdHocCommandActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = AdHocCommand
    relationship = 'activitystream_set'
    new_in_220 = True


class AdHocCommandNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = AdHocCommand
    relationship = 'notifications'
    new_in_300 = True


class AdHocCommandStdout(UnifiedJobStdout):

    model = AdHocCommand
    new_in_220 = True
