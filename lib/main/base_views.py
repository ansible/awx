# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# All rights reserved

from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from lib.main.models import *
from django.contrib.auth.models import User
from lib.main.serializers import *
from lib.main.rbac import *
from lib.main.access import *
from rest_framework.exceptions import PermissionDenied
from rest_framework import mixins
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
import exceptions
import datetime
import json as python_json

# FIXME: machinery for auto-adding audit trail logs to all CREATE/EDITS

class BaseList(generics.ListCreateAPIView):

    permission_classes = (CustomRbac,)

    # Subclasses should define:
    #   model = ModelClass
    #   serializer_class = SerializerClass

    def post(self, request, *args, **kwargs):
        # FIXME: Should  inherit from generics.ListAPIView if not postable.
        postable = getattr(self.__class__, 'postable', True)
        if not postable:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super(BaseList, self).post(request, *args, **kwargs)

    # NOTE: Moved filtering from get_queryset into custom filter backend.

class BaseSubList(BaseList):

    ''' used for subcollections with an overriden post '''

    # Subclasses should define at least:
    #   model = ModelClass
    #   serializer_class = SerializerClass
    #   parent_model = ModelClass
    #   relationship = 'rel_name_from_parent_to_model'
    # And optionally:
    #   postable = True/False
    #   inject_primary_key_on_post_as = 'field_on_model_referring_to_parent'
    #   severable = True/False

    def post(self, request, *args, **kwargs):

        # decide whether to return 201 with data (new object) or 204 (just associated)
        created = False
        ser = None

        postable = getattr(self.__class__, 'postable', False)
        if not postable:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        # Make a copy of the data provided (since it's readonly) in order to
        # inject additional data.
        if hasattr(request.DATA, 'dict'):
            data = request.DATA.dict()
        else:
            data = request.DATA
        parent_id = kwargs['pk']
        sub_id = data.get('id', None)
        main = self.__class__.parent_model.objects.get(pk=parent_id)
        severable = getattr(self.__class__, 'severable', True)

        subs = None

        if sub_id:
            subs = self.__class__.model.objects.filter(pk=sub_id)
        else:
            if 'disassociate' in data:
                raise PermissionDenied() # ID is required to disassociate
            else:

                # this is a little tricky and a little manual
                # the object ID was not specified, so it probably doesn't exist in the DB yet.
                # we want to see if we can create it.  The URL may choose to inject it's primary key into the object
                # because we are posting to a subcollection. Use all the normal access control mechanisms.

                inject_primary_key = getattr(self.__class__, 'inject_primary_key_on_post_as', None)

                if inject_primary_key is not None:

                    # add the key to the post data using the pk from the URL
                    data[inject_primary_key] = kwargs['pk']

                    # attempt to deserialize the object
                    ser = self.__class__.serializer_class(data=data)
                    if not ser.is_valid():
                        return Response(status=status.HTTP_400_BAD_REQUEST, data=ser.errors)

                    if not check_user_access(request.user, self.model, 'add', ser.init_data):
                        raise PermissionDenied()

                    # save the object through the serializer, reload and returned the saved object deserialized
                    obj = ser.save()
                    ser = self.__class__.serializer_class(obj)

                    # now make sure we could have already attached the two together.  If we could not have, raise an exception
                    # such that the transaction does not commit.

                    if main == obj:
                        # no attaching to yourself
                        raise PermissionDenied()

                    if self.__class__.parent_model != User:

                        # FIXME: refactor into smaller functions

                        if obj.__class__ in [ User]:
                            if self.__class__.parent_model == Organization:
                                # user can't inject an organization because it's not part of the user
                                # model so we have to cheat here.  This may happen for other cases
                                # where we are creating a user immediately on a subcollection
                                # when that user does not already exist.  Relations will work post-save.
                                organization = Organization.objects.get(pk=data[inject_primary_key])
                                if not request.user.is_superuser:
                                    if not organization.admins.filter(pk=request.user.pk).count() > 0:
                                        raise PermissionDenied()
                            else:
                                raise exceptions.NotImplementedError()
                        else:
                            if not check_user_access(request.user, type(obj), 'read', obj):
                                raise PermissionDenied()
                        # If we just created a new object, we may not yet be able to read it because it's not yet associated with its parent model.
                        if not check_user_access(request.user, self.parent_model, 'attach', main, obj, self.relationship, data, skip_sub_obj_read_check=True):
                            raise PermissionDenied()

                        # FIXME: manual attachment code neccessary for users here, move this into the main code.
                        # this is because users don't have FKs into what they are attaching. (also refactor)

                        if self.__class__.parent_model == Organization:
                             organization = Organization.objects.get(pk=data[inject_primary_key])
                             import lib.main.views
                             if self.__class__ == lib.main.views.OrganizationsUsersList:
                                 organization.users.add(obj)
                             elif self.__class__ == lib.main.views.OrganizationsAdminsList:
                                 organization.admins.add(obj)

                    else:
                        if not check_user_access(request.user, type(obj), 'read', obj):
                            raise PermissionDenied()
                        # FIXME: should generalize this
                        if not check_user_access(request.user, self.parent_model, 'attach', main, obj, self.relationship, data):
                            raise PermissionDenied()

                    # why are we returning here?
                    # return Response(status=status.HTTP_201_CREATED, data=ser.data)
                    created = True 
                    subs = [ obj ]

                else:

                    # view didn't specify a way to get the pk from the URL, so not even trying
                    return Response(status=status.HTTP_400_BAD_REQUEST, data=python_json.dumps(dict(msg='object cannot be created')))

        # we didn't have to create the object, so this is just associating the two objects together now...
        # (or disassociating them)

        if len(subs) != 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        sub = subs[0]
        relationship = getattr(main, self.__class__.relationship)

        if not 'disassociate' in data:
            if not request.user.is_superuser:
                if type(main) != User:
                    #if not self.__class__.parent_model.can_user_attach(request.user, main, sub, self.__class__.relationship, data):
                    if not check_user_access(request.user, self.parent_model, 'attach', main, sub, self.relationship, data):
                        raise PermissionDenied()
                else:
		            #if not UserHelper.can_user_attach(request.user, main, sub, self.__class__.relationship, data):
                    if not check_user_access(request.user, self.parent_model, 'attach', main, sub, self.relationship, data):
                        raise PermissionDenied()

            if sub not in relationship.all():
                relationship.add(sub)
        else:
            if not request.user.is_superuser:
                if type(main) != User:
                     #if not self.__class__.parent_model.can_user_unattach(request.user, main, sub, self.__class__.relationship):
                     if not check_user_access(request.user, self.parent_model, 'unattach', main, sub, self.relationship):
                         raise PermissionDenied()
                else:
                     #if not UserHelper.can_user_unattach(request.user, main, sub, self.__class__.relationship):
                     if not check_user_access(request.user, self.parent_model, 'unattach', main, sub, self.relationship):
                         raise PermissionDenied()


            if severable:
                relationship.remove(sub)
            else:
                # resource is just a ForeignKey, can't remove it from the set, just set it inactive
                sub.name   = "_deleted_%s_%s" % (str(datetime.time()), sub.name)
                sub.active = False
                sub.save()

        if created:
            return Response(status=status.HTTP_201_CREATED, data=ser.data)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)


class BaseDetail(generics.RetrieveUpdateDestroyAPIView):

    def pre_save(self, obj):
        if type(obj) not in [ User, Tag, AuditTrail ]:
            obj.created_by = self.request.user

    def destroy(self, request, *args, **kwargs):
        # somewhat lame that delete has to call it's own permissions check
        obj = self.model.objects.get(pk=kwargs['pk'])
        # FIXME: Why isn't the active check being caught earlier by RBAC?
        if getattr(obj, 'active', True) == False:
            raise Http404()
        if getattr(obj, 'is_active', True) == False:
            raise Http404()
        #if not request.user.is_superuser and not self.delete_permissions_check(request, obj):
        if not check_user_access(request.user, self.model, 'delete', obj):
            raise PermissionDenied()
        if isinstance(obj, PrimordialModel):
            obj.name   = "_deleted_%s_%s" % (str(datetime.time()), obj.name)
            obj.active = False
            obj.save()
        elif type(obj) == User:
            obj.username  = "_deleted_%s_%s" % (str(datetime.time()), obj.username)
            obj.is_active = False
            obj.save()
        else:
            raise Exception("InternalError: destroy() not implemented yet for %s" % obj)
        return HttpResponse(status=204)

    def put(self, request, *args, **kwargs):
        self.put_filter(request, *args, **kwargs)
        return super(BaseDetail, self).put(request, *args, **kwargs)

    def put_filter(self, request, *args, **kwargs):
        ''' scrub any fields the user cannot/should not put, based on user context.  This runs after read-only serialization filtering '''
        pass

class VariableBaseDetail(BaseDetail):
    '''
    an object that is always 1 to 1 with the foreign key of another object
    and does not have it's own key, such as HostVariableDetail
    '''

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied()

    def put(self, request, *args, **kwargs):
        # FIXME: lots of overlap between put and get here, need to refactor

        through_obj = self.__class__.parent_model.objects.get(pk=kwargs['pk'])

        #has_permission = Inventory._has_permission_types(request.user, through_obj.inventory, PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE)
        #if not has_permission:
        #    raise PermissionDenied()
        if not check_user_access(request.user, Inventory, 'change', through_obj.inventory, None):
            raise PermissionDenied

        this_object = None

        if hasattr(request.DATA, 'dict'):
            data = request.DATA.dict()
        else:
            data = request.DATA

        try:
            this_object = getattr(through_obj, self.__class__.reverse_relationship, None)
        except:
            pass

        if this_object is None:
            this_object = self.__class__.model.objects.create(data=python_json.dumps(data))
        else:
            this_object.data = python_json.dumps(data)
            this_object.save()
        setattr(through_obj, self.__class__.reverse_relationship, this_object)
        through_obj.save()

        return Response(status=status.HTTP_200_OK, data=python_json.loads(this_object.data))


    def get(self, request, *args, **kwargs):

        # if null, recreate a blank object
        through_obj = self.__class__.parent_model.objects.get(pk=kwargs['pk'])
        this_object = None

        try:
            this_object = getattr(through_obj, self.__class__.reverse_relationship, None)
        except Exception, e:
            pass

        if this_object is None:
            new_args               = {}
            new_args['data']       = python_json.dumps(dict())
            this_object            = self.__class__.model.objects.create(**new_args)
            setattr(through_obj, self.__class__.reverse_relationship, this_object)
            through_obj.save()

        #has_permission = Inventory._has_permission_types(request.user, through_obj.inventory, PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE)
        #if not has_permission:
        #    raise PermissionDenied()
        if not check_user_access(request.user, Inventory, 'read', through_obj.inventory):
            raise PermissionDenied

        return Response(status=status.HTTP_200_OK, data=python_json.loads(this_object.data))

