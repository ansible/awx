# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# 
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License. 
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.

from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from lib.main.models import *
from django.contrib.auth.models import User
from lib.main.serializers import *
from lib.main.rbac import *
from django.core.exceptions import PermissionDenied
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

    def list_permissions_check(self, request, obj=None):
        ''' determines some early yes/no access decisions, pre-filtering '''
        if request.method == 'GET':
             return True
        if request.method == 'POST':
             if self.__class__.model in [ User ]:
                  ok = request.user.is_superuser or (request.user.admin_of_organizations.count() > 0)
                  if not ok:
                      raise PermissionDenied()
                  return True
             else:
                  if not self.__class__.model.can_user_add(request.user, self.request.DATA):
                      raise PermissionDenied()
                  return True
        raise exceptions.NotImplementedError

    def get_queryset(self):
        base = self._get_queryset()
        model = self.__class__.model
        if model == User:
            return base.filter(is_active=True)
        elif model in [ Tag, AuditTrail ]:
            return base
        else:
            return self._get_queryset().filter(active=True)



class BaseSubList(BaseList):

    ''' used for subcollections with an overriden post '''

    def list_permissions_check(self, request, obj=None):
        ''' determines some early yes/no access decisions, pre-filtering '''
        if request.method == 'GET':
             return True
        if request.method == 'POST':
             # the can_user_attach methods will be called below
             return True
        raise exceptions.NotImplementedError


    def post(self, request, *args, **kwargs):

        postable = getattr(self.__class__, 'postable', False)
        if not postable:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        parent_id = kwargs['pk']
        sub_id = request.DATA.get('id', None)
        main = self.__class__.parent_model.objects.get(pk=parent_id)
        severable = getattr(self.__class__, 'severable', True)

        subs = None

        if sub_id:
            subs = self.__class__.model.objects.filter(pk=sub_id)
        else:
            if 'disassociate' in request.DATA:
                raise PermissionDenied() # ID is required to disassociate
            else:

                # this is a little tricky and a little manual
                # the object ID was not specified, so it probably doesn't exist in the DB yet.
                # we want to see if we can create it.  The URL may choose to inject it's primary key into the object
                # because we are posting to a subcollection. Use all the normal access control mechanisms.

                inject_primary_key = getattr(self.__class__, 'inject_primary_key_on_post_as', None)

                if inject_primary_key is not None:

                    # add the key to the post data using the pk from the URL
                    request.DATA[inject_primary_key] = kwargs['pk']

                    # attempt to deserialize the object
                    ser = self.__class__.serializer_class(data=request.DATA)
                    if not ser.is_valid():
                        return Response(status=status.HTTP_400_BAD_REQUEST, data=ser.errors)

                    # ask the usual access control settings
                    if not self.__class__.model.can_user_add(request.user, ser.init_data):
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
                        if not self.__class__.parent_model.can_user_attach(request.user, main, obj, self.__class__.relationship):
                            raise PermissionDenied()
                    else:
                        # FIXME: should generalize this
                        if not UserHelper.can_user_attach(request.user, main, obj, self.__class__.relationship):
                            raise PermissionDenied()

                    return Response(status=status.HTTP_201_CREATED, data=ser.data)

                else:

                    # view didn't specify a way to get the pk from the URL, so not even trying
                    return Response(status=status.HTTP_400_BAD_REQUEST, data=python_json.dumps(dict(msg='object cannot be created')))

        # we didn't have to create the object, so this is just associating the two objects together now...
        # (or disassociating them)

        if len(subs) != 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        sub = subs[0]
        relationship = getattr(main, self.__class__.relationship)

        if not 'disassociate' in request.DATA:
            if not request.user.is_superuser:
                if type(main) != User:
                    if not self.__class__.parent_model.can_user_attach(request.user, main, sub, self.__class__.relationship):
                        raise PermissionDenied()
                else:
		    if not UserHelper.can_user_attach(request.user, main, sub, self.__class__.relationship):
                        raise PermissionDenied()

            if sub in relationship.all():
                return Response(status=status.HTTP_409_CONFLICT)
            relationship.add(sub)
        else:
            if not request.user.is_superuser:
                if type(main) != User:
                     if not self.__class__.parent_model.can_user_unattach(request.user, main, sub, self.__class__.relationship):
                         raise PermissionDenied()
                else:
                     if not UserHelper.can_user_unattach(request.user, main, sub, self.__class__.relationship):
                         raise PermissionDenied()


            if severable:
                relationship.remove(sub)
            else:
                # resource is just a ForeignKey, can't remove it from the set, just set it inactive
                sub.name   = "_deleted_%s_%s" % (str(datetime.time()), sub.name)
                sub.active = False
                sub.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseDetail(generics.RetrieveUpdateDestroyAPIView):

    def pre_save(self, obj):
        if type(obj) not in [ User, Tag, AuditTrail ]:
            obj.created_by = self.request.user

    def destroy(self, request, *args, **kwargs):
        # somewhat lame that delete has to call it's own permissions check
        obj = self.model.objects.get(pk=kwargs['pk'])
        if getattr(obj, 'active', True) == False:
            raise Http404()
        if getattr(obj, 'is_active', True) == False:
            raise Http404()
        if not request.user.is_superuser and not self.delete_permissions_check(request, obj):
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

    def delete_permissions_check(self, request, obj):
        if isinstance(obj, PrimordialModel):
            return self.__class__.model.can_user_delete(request.user, obj)
        elif isinstance(obj, User):
            return UserHelper.can_user_delete(request.user, obj)
        raise PermissionDenied()


    def item_permissions_check(self, request, obj):

        if request.method == 'GET':
            if type(obj) == User:
                return UserHelper.can_user_read(request.user, obj)
            else:
                return self.__class__.model.can_user_read(request.user, obj)
        elif request.method in [ 'PUT' ]:
            if type(obj) == User:
                return UserHelper.can_user_administrate(request.user, obj)
            else:
                return self.__class__.model.can_user_administrate(request.user, obj)
        return False

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

    def delete_permissions_check(self, request, obj):
        raise PermissionDenied()

    def item_permissions_check(self, request, obj):
        through_obj = self.__class__.parent_model.objects.get(pk = self.request.args['pk'])
        if request.method == 'GET':
            return self.__class__.parent_model.can_user_read(request.user, through_obj)
        elif request.method in [ 'PUT' ]:
            return self.__class__.parent_model.can_user_administrate(request.user, through_obj)
        return False

    def put(self, request, *args, **kwargs):
        # FIXME: lots of overlap between put and get here, need to refactor

        through_obj = self.__class__.parent_model.objects.get(pk=kwargs['pk'])

        has_permission = Inventory._has_permission_types(request.user, through_obj.inventory, PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE)

        if not has_permission:
            raise PermissionDenied()

        this_object = None

        try:
            this_object = getattr(through_obj, self.__class__.reverse_relationship, None)
        except:
            pass

        if this_object is None:
            this_object = self.__class__.model.objects.create(data=python_json.dumps(request.DATA))
        else:
            this_object.data = python_json.dumps(request.DATA)
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

        has_permission = Inventory._has_permission_types(request.user, through_obj.inventory, PERMISSION_TYPES_ALLOWING_INVENTORY_WRITE)
        if not has_permission:
            raise PermissionDenied()
        return Response(status=status.HTTP_200_OK, data=python_json.loads(this_object.data))

