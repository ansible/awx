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

    # FIXME: use this for the audit trail hook, ideally in base class.
    #def pre_save(self, obj):
    #   obj.owner = self.request.user

    def item_permissions_check(self, request, obj):
        is_admin = request.user in obj.admins.all() 
        is_user  = request.user in obj.users.all()
        
        if request.method == 'GET':
            return is_admin or is_user
        elif request.method in [ 'PUT' ]:
            return is_admin
        return False

    def delete_permissions_check(self, request, obj):
        return request.user in obj.admins.all() 

class OrganizationsAuditTrailList(BaseList):

    model = AuditTrail
    serializer_class = AuditTrailSerializer
    permission_classes = (CustomRbac,)

    # FIXME: guts & tests
    pass

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


class OrganizationsProjectsList(BaseList):
    
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)
    
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

    # BOOKMARK
    def post(self, request, *args, **kwargs):

        # POST { pk: 7, disassociate: True }

        organization_id = kwargs['pk']
        project_id = request.DATA.get('id')
        organization = Organization.objects.get(pk=organization_id)
        projects = Project.objects.filter(pk=project_id)
        if len(projects) != 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        project = projects[0]

        # you can only add a project to an organization if you are a superuser or
        # the person who created the project.  TODO -- want to defer this question
        # to the model. (FIXME)

        if not 'disassociate' in request.DATA:
            # admin of another org can't add a project to their org
            if not request.user.is_superuser or project.created_by == request.user:
                raise PermissionDenied()
            if project in organization.projects.all():
                return Response(status=status.HTTP_409_CONFLICT)
            organization.projects.add(project)
        else:
            # to disassociate, be the org admin or a superuser
            # FIXME: sprinkle these throughout the object layer & simplify
            if not request.user.is_superuser and not project.can_user_administrate(request.user):
                raise PermissionDenied()
            organization.projects.remove(project)
            # multiple attempts to delete the same thing aren't an error, we're cool
        return Response(status=status.HTTP_204_NO_CONTENT)





class OrganizationsTagsList(BaseList):
    # FIXME: guts & tests
    pass

class ProjectsDetail(BaseDetail):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)

    def item_permissions_check(self, request, obj):

        # to get, must be in a team assigned to this project
        # or be an org admin of an org this project is in

        raise exceptions.NotImplementedError()

        #is_admin = request.user in obj.admins.all()
        #is_user  = request.user in obj.users.all()
        #
        #if request.method == 'GET':
        #    return is_admin or is_user
        #elif request.method in [ 'PUT' ]:
        #    return is_admin
        #return False

    def delete_permissions_check(self, request, obj):
        # FIXME: logic TBD
        raise exceptions.NotImplementedError()
        #return request.user in obj.admins.all()

