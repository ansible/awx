# (c) 2013, AnsibleWorks, Michael DeHaan <michael@ansibleworks.com>
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander.  If not, see <http://www.gnu.org/licenses/>.

from django.http import HttpResponse
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

# FIXME: machinery for auto-adding audit trail logs to all CREATE/EDITS

class BaseList(generics.ListCreateAPIView):
 
    def list_permissions_check(self, request, obj=None):
        ''' determines some early yes/no access decisions, pre-filtering '''
        if request.method == 'GET':
             return True
        if request.method == 'POST':
             if self.__class__.model in [ User ]:
                  # Django user gets special handling since it's not our class
                  # org admins are allowed to create users
                  return self.request.user.is_superuser or (self.request.user.admin_of_organizations.count() > 0)
             else:
                  return self.__class__.model.can_user_add(request.user)
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
        sub_id = request.DATA.get('id')
        main = self.__class__.parent_model.objects.get(pk=parent_id)
        subs = self.__class__.model.objects.filter(pk=sub_id)
        if len(subs) != 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        sub = subs[0]
        relationship = getattr(main, self.__class__.relationship)
  
        if not 'disassociate' in request.DATA:
            if not request.user.is_superuser and not self.__class__.parent_model.can_user_attach(request.user, main, sub, self.__class__.relationship):
                raise PermissionDenied()
            if sub in relationship.all():
                return Response(status=status.HTTP_409_CONFLICT)
            relationship.add(sub)
        else:
            if not request.user.is_superuser and not self.__class__.parent_model.can_user_unattach(request.user, main, sub, self.__class__.relationship):
                raise PermissionDenied()
            relationship.remove(sub)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseDetail(generics.RetrieveUpdateDestroyAPIView):

    def pre_save(self, obj):
        if type(obj) not in [ User, Tag, AuditTrail ]:
            obj.created_by = self.request.user

    def destroy(self, request, *args, **kwargs):
        # somewhat lame that delete has to call it's own permissions check
        obj = self.model.objects.get(pk=kwargs['pk'])
        if not request.user.is_superuser and not self.delete_permissions_check(request, obj):
            raise PermissionDenied()
        if isinstance(obj, CommonModel):
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
        if isinstance(obj, CommonModel):
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


