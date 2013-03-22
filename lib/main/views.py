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
from base_views import BaseList, BaseDetail, BaseSubList

class OrganizationsList(BaseList):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)

    # I can see the organizations if:
    #   I am a superuser
    #   I am an admin of the organization 
    #   I am a member of the organization
   
    def _get_queryset(self):
        if self.request.user.is_superuser:
            return Organization.objects.all()
        return Organization.objects.filter(
            admins__in = [ self.request.user ]
        ).distinct() | Organization.objects.filter(
            users__in = [ self.request.user ]
        ).distinct()

class OrganizationsDetail(BaseDetail):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)

class OrganizationsAuditTrailList(BaseList):

    model = AuditTrail
    serializer_class = AuditTrailSerializer
    permission_classes = (CustomRbac,)

class OrganizationsUsersList(BaseList):
    
    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)

    # I can see the users in the organization if:
    #    I am a super user
    #    I am an admin of the organization

    def _get_queryset(self):
        # FIXME:
        base = User.objects.all(organizations__pk__in = [ self.kwargs.get('pk') ])
        if self.request.user.is_superuser:
            return base.all()
        return base.objects.filter(
            organizations__organization__admins__in = [ self.request.user ]
        ).distinct() 


class OrganizationsAdminsList(BaseList):
    
    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)

    # I can see the admins in the organization if:
    #    I am a super user
    #    I am an admin of the organization
    
    def _get_queryset(self):

        # FIXME
        base = User.objects.all(admin_of_organizations__pk__in = [ self.kwargs.get('pk') ])

        if self.request.user.is_superuser:
            return base.all()
        return base.filter(
            organizations__organization__admins__in = [ self.request.user ]
        ).distinct() 


class OrganizationsProjectsList(BaseSubList):
    
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)

    parent_model = Organization  # for sub list
    relationship = 'projects'    # " "
    
    # I can see the projects from the organization if:
    #    I'm the superuser
    #    I am a an administrator of the organization
    #    I am a member of a team on the project

    def _get_queryset(self):
        base = Project.objects.filter(organizations__in = [ self.kwargs.get('pk') ])
        if self.request.user.is_superuser:
            return base.all()
        return base.filter(
            organizations__admins__in = [ self.request.user ]
        ).distinct() | base.filter(
            teams__users__in = [ self.request.user ]
        ).distinct()

class OrganizationsTagsList(BaseList):
    # FIXME: guts & tests
    pass

class ProjectsDetail(BaseDetail):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)



