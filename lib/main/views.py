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
        ''' I can see organizations when I am a superuser, or I am an admin or user in that organization '''
        base = Organization.objects
        if self.request.user.is_superuser:
            return base.all()
        return base.filter(
            admins__in = [ self.request.user ]
        ).distinct() | base.filter(
            users__in = [ self.request.user ]
        ).distinct()

class OrganizationsDetail(BaseDetail):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)

class OrganizationsAuditTrailList(BaseSubList):

    model = AuditTrail
    serializer_class = AuditTrailSerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization
    relationship = 'audit_trail'
    postable = False

    def _get_queryset(self):
        ''' to list tags in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not (self.request.user.is_superuser or self.request.user in organization.admins.all()):
            # FIXME: use: organization.can_user_administrate(self.request.user)
            raise PermissionDenied()
        return AuditTrail.objects.filter(organization_by_audit_trail__in = [ organization ])


class OrganizationsUsersList(BaseSubList):
    
    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization
    relationship = 'users'
    postable = True

    def _get_queryset(self):
        ''' to list users in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not self.request.user.is_superuser and not self.request.user in organization.admins.all():
            raise PermissionDenied()
        return User.objects.filter(organizations__in = [ organization ])

class OrganizationsAdminsList(BaseSubList):
    
    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization
    relationship = 'admins'
    postable = True

    def _get_queryset(self):
        ''' to list admins in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not self.request.user.is_superuser and not self.request.user in organization.admins.all():
            raise PermissionDenied()
        return User.objects.filter(admin_of_organizations__in = [ organization ])

class OrganizationsProjectsList(BaseSubList):
    
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization  # for sub list
    relationship = 'projects'    # " "
    postable = True
    
    def _get_queryset(self):
        ''' to list projects in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not (self.request.user.is_superuser or self.request.user in organization.admins.all()):
            raise PermissionDenied()
        return Project.objects.filter(organizations__in = [ organization ])

class OrganizationsTagsList(BaseSubList):
    
    model = Tag
    serializer_class = TagSerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization  # for sub list
    relationship = 'tags'        # " "
    postable = True

    def _get_queryset(self):
        ''' to list tags in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not (self.request.user.is_superuser or self.request.user in organization.admins.all()):
            # FIXME: use: organization.can_user_administrate(self.request.user)
            raise PermissionDenied()
        return Tag.objects.filter(organization_by_tag__in = [ organization ])

class ProjectsDetail(BaseDetail):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)

class TagsDetail(BaseDetail):

    model = Tag
    serializer_class = TagSerializer
    permission_classes = (CustomRbac,)


