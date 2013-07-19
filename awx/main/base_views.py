# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json

# Django
from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.timezone import now

# Django REST Framework
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

# AWX
from awx.main.models import *

# FIXME: machinery for auto-adding audit trail logs to all CREATE/EDITS

class ListAPIView(generics.ListAPIView):
    # Base class for a read-only list view.

    # Subclasses should define:
    #   model = ModelClass
    #   serializer_class = SerializerClass

    def get_queryset(self):
        return self.request.user.get_queryset(self.model)

class ListCreateAPIView(ListAPIView, generics.ListCreateAPIView):
    # Base class for a list view that allows creating new objects.
    pass

class SubListAPIView(ListAPIView):
    # Base class for a read-only sublist view.

    # Subclasses should define at least:
    #   model = ModelClass
    #   serializer_class = SerializerClass
    #   parent_model = ModelClass
    #   relationship = 'rel_name_from_parent_to_model'
    # And optionally (user must have given access permission on parent object
    # to view sublist):
    #   parent_access = 'admin'

    def get_parent_object(self):
        parent_filter = {
            self.lookup_field: self.kwargs.get(self.lookup_field, None),
        }
        return get_object_or_404(self.parent_model, **parent_filter)

    def check_parent_access(self, parent=None):
        parent = parent or self.get_parent_object()
        parent_access = getattr(self, 'parent_access', 'admin')
        if parent_access in ('read', 'delete'):
            args = (self.parent_model, parent_access, parent)
        else:
            args = (self.parent_model, parent_access, parent, None)
        if not self.request.user.can_access(*args):
            raise PermissionDenied()

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model).distinct()
        sublist_qs = getattr(parent, self.relationship).distinct()
        return qs & sublist_qs

class SubListCreateAPIView(SubListAPIView, generics.ListCreateAPIView):
    # Base class for a sublist view that allows for creating subobjects and
    # attaching/detaching them from the parent.

    # In addition to SubListAPIView properties, subclasses may define:
    #   inject_primary_key_on_post_as = 'field_on_model_referring_to_parent'
    #   severable = True/False

    def create(self, request, *args, **kwargs):
        # If the object ID was not specified, it probably doesn't exist in the
        # DB yet. We want to see if we can create it.  The URL may choose to
        # inject it's primary key into the object because we are posting to a
        # subcollection. Use all the normal access control mechanisms.

        inject_primary_key = getattr(self, 'inject_primary_key_on_post_as', None)

        if inject_primary_key is None:
            # view didn't specify a way to get the pk from the URL, so not even trying
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data=dict(msg='object cannot be created'))

        # Make a copy of the data provided (since it's readonly) in order to
        # inject additional data.
        if hasattr(request.DATA, 'dict'):
            data = request.DATA.dict()
        else:
            data = request.DATA

        # add the key to the post data using the pk from the URL
        data[inject_primary_key] = kwargs['pk']

        # attempt to deserialize the object
        serializer = self.serializer_class(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        # Verify we have permission to add the object as given.
        if not request.user.can_access(self.model, 'add', serializer.init_data):
            raise PermissionDenied()

        # save the object through the serializer, reload and returned the saved object deserialized
        obj = serializer.save()
        serializer = self.serializer_class(obj)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def attach(self, request, *args, **kwargs):
        created = False
        parent = self.get_parent_object()
        relationship = getattr(parent, self.relationship)
        sub_id = request.DATA.get('id', None)
        data = request.DATA

        # Create the sub object if an ID is not provided.
        if not sub_id:
            response = self.create(request, *args, **kwargs)
            if response.status_code != status.HTTP_201_CREATED:
                return response
            sub_id = response.data['id']
            data = response.data
            created = True

        # Retrive the sub object (whether created or by ID).
        try:
            sub = self.model.objects.get(pk=sub_id)
        except self.model.DoesNotExist:
            data = dict(msg='Object with id %s cannot be found' % sub_id)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
            
        # Verify we have permission to attach.
        if not request.user.can_access(self.parent_model, 'attach', parent, sub, self.relationship, data, skip_sub_obj_read_check=created):
            raise PermissionDenied()

        # Attach the object to the collection.
        if sub not in relationship.all():
            relationship.add(sub)

        if created:
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def unattach(self, request, *args, **kwargs):
        sub_id = request.DATA.get('id', None)
        if not sub_id:
            data = dict(msg='"id" is required to disassociate')
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        parent = self.get_parent_object()
        severable = getattr(self, 'severable', True)
        relationship = getattr(parent, self.relationship)

        try:
            sub = self.model.objects.get(pk=sub_id)
        except self.model.DoesNotExist:
            data = dict(msg='Object with id %s cannot be found' % sub_id)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.can_access(self.parent_model, 'unattach', parent, sub, self.relationship):
            raise PermissionDenied()

        if severable:
            relationship.remove(sub)
        else:
            # resource is just a ForeignKey, can't remove it from the set, just set it inactive
            sub.mark_inactive()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, *args, **kwargs):
        if 'disassociate' in request.DATA:
            return self.unattach(request, *args, **kwargs)
        else:
            return self.attach(request, *args, **kwargs)


class RetrieveAPIView(generics.RetrieveAPIView):
    pass

class RetrieveUpdateDestroyAPIView(RetrieveAPIView, generics.RetrieveUpdateDestroyAPIView):

    def pre_save(self, obj):
        if type(obj) not in [ User ]:
            obj.created_by = self.request.user

    def destroy(self, request, *args, **kwargs):
        # somewhat lame that delete has to call it's own permissions check
        obj = self.model.objects.get(pk=kwargs['pk'])
        # FIXME: Why isn't the active check being caught earlier by RBAC?
        if getattr(obj, 'active', True) == False:
            raise Http404()
        if getattr(obj, 'is_active', True) == False:
            raise Http404()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        if hasattr(obj, 'mark_inactive'):
            obj.mark_inactive()
        else:
            raise Exception("InternalError: destroy() not implemented yet for %s" % obj)
        return HttpResponse(status=204)

    def update(self, request, *args, **kwargs):
        self.update_filter(request, *args, **kwargs)
        return super(RetrieveUpdateDestroyAPIView, self).update(request, *args, **kwargs)

    def update_filter(self, request, *args, **kwargs):
        ''' scrub any fields the user cannot/should not put/patch, based on user context.  This runs after read-only serialization filtering '''
        pass
