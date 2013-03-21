from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from lib.main.models import *
from lib.main.serializers import *
from lib.main.rbac import *
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from rest_framework import mixins
from rest_framework import generics
from rest_framework import permissions
import exceptions
import datetime

# FIXME: machinery for auto-adding audit trail logs to all CREATE/EDITS

class BaseList(generics.ListCreateAPIView):
  
    def list_permissions_check(self, request, obj=None):
        if request.method == 'GET':
             # everybody can call get, but it's filtered
             return True
        if request.method == 'POST':
             # superusers have already been cleared, so deny regular users
             return False
        raise exceptions.NotImplementedError
    
    def get_queryset(self):
        return self._get_queryset().filter(active=True)    

class BaseDetail(generics.RetrieveUpdateDestroyAPIView):

    def destroy(self, request, *args, **kwargs):
        # somewhat lame that delete has to call it's own permissions check
        obj = self.model.objects.get(pk=kwargs['pk'])
        if not request.user.is_superuser and not self.delete_permissions_check(request, obj):
            raise PermissionDenied()
        obj.name   = "_deleted_%s_%s" % (str(datetime.time()), obj.name)
        obj.active = False
        obj.save()
        return HttpResponse(status=204)

class OrganizationsList(BaseList):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)
   
    def _get_queryset(self):

        if self.request.user.is_superuser:
            return Organization.objects.filter(active=True)

        return Organization.objects.filter(
            admins__in = [ self.request.user.application_user ]
        ).distinct() | Organization.objects.filter(
            users__in = [ self.request.user.application_user ]
        ).distinct()

class OrganizationsDetail(BaseDetail):

    model = Organization
    serializer_class = OrganizationSerializer

    permission_classes = (CustomRbac,)

    # FIXME: use this for the audit trail hook, ideally in base class.
    #def pre_save(self, obj):
    #   obj.owner = self.request.user

    def item_permissions_check(self, request, obj):
        is_admin = request.user.application_user in obj.admins.all() 
        is_user  = request.user.application_user in obj.users.all()
        
        if request.method == 'GET':
            return is_admin or is_user
        elif request.method in [ 'PUT' ]:
            return is_admin
        return False

    def delete_permissions_check(self, request, obj):
        return request.user.application_user in obj.admins.all() 

class OrganizationsAuditTrailList(BaseList):
    # FIXME: implementation and tests
    pass

class OrganizationsUsersList(BaseList):
    # FIXME: implementation and tests
    pass

class OrganizationsAdminsList(BaseList):
    # FIXME: implementation and tests
    pass

class OrganizationsProjectsList(BaseList):
    # FIXME: implementation and tests
    pass

class OrganizationsTagsList(BaseList):
    pass


