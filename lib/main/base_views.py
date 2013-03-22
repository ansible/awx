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

class BaseDetail(generics.RetrieveUpdateDestroyAPIView):

    def pre_save(self, obj):
       obj.created_by = owner = self.request.user

    def destroy(self, request, *args, **kwargs):
        # somewhat lame that delete has to call it's own permissions check
        obj = self.model.objects.get(pk=kwargs['pk'])
        if not request.user.is_superuser and not self.delete_permissions_check(request, obj):
            raise PermissionDenied()
        obj.name   = "_deleted_%s_%s" % (str(datetime.time()), obj.name)
        obj.active = False
        obj.save()
        return HttpResponse(status=204)

