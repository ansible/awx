from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from lib.main.models import *
from lib.main.serializers import *
from lib.main.rbac import *
from django.contrib.auth.models import AnonymousUser
from rest_framework import mixins
from rest_framework import generics
from rest_framework import permissions
import exceptions

class OrganizationsList(generics.ListCreateAPIView):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)

    #def pre_save(self, obj):
    #   obj.owner = self.request.user
   
    def get_queryset(self):

        if self.request.user.is_superuser:
            return Organization.objects.filter(active=True)
        return Organization.objects.filter(active = True, admins__in = [ self.request.user.application_user ]).distinct() | \
               Organization.objects.filter(active = True, users__in = [ self.request.user.application_user ]).distinct()

    def permissions_check(self, request, obj):
        raise exceptions.NotImplementedError

 
class OrganizationsDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Organization
    serializer_class = OrganizationSerializer

    permission_classes = (CustomRbac,)

    #def pre_save(self, obj):
    #   obj.owner = self.request.user

    def permissions_check(self, request, obj):
         admin = request.user.application_user in obj.admins.all() 
         user  = request.user.application_user in obj.users.all()
         if request.method == 'GET':
              return admin or user
         if request.method == 'PUT':
              return admin
