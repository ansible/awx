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
             return False
        raise exceptions.NotImplementedError
   
    def get_queryset(self):
        return self._get_queryset().filter(active=True)

class BaseSubList(BaseList):

    ''' used for subcollections with an overriden post '''

    def post(self, request, *args, **kwargs):

        parent_id = kwargs['pk']
        sub_id = request.DATA.get('id')
        main = self.__class__.parent_model.objects.get(pk=parent_id)
        subs = self.__class__.model.objects.filter(pk=sub_id)
        if len(subs) != 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        sub = subs[0]
        relationship = getattr(main, self.__class__.relationship)
  
        if not 'disassociate' in request.DATA:
            if not request.user.is_superuser or not self.__class__.parent_model.can_user_attach(request.user, main, sub, self.__class__.relationship):
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
        obj.created_by = self.request.user

    def destroy(self, request, *args, **kwargs):
        # somewhat lame that delete has to call it's own permissions check
        obj = self.model.objects.get(pk=kwargs['pk'])
        if not request.user.is_superuser and not self.delete_permissions_check(request, obj):
            raise PermissionDenied()
        obj.name   = "_deleted_%s_%s" % (str(datetime.time()), obj.name)
        obj.active = False
        obj.save()
        return HttpResponse(status=204)

    def delete_permissions_check(self, request, obj):
        return self.__class__.model.can_user_delete(request.user, obj)

    def item_permissions_check(self, request, obj):

        if request.method == 'GET':
            return self.__class__.model.can_user_read(request.user, obj)
        elif request.method in [ 'PUT' ]:
            return self.__class__.model.can_user_administrate(request.user, obj)
        return False



