# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import re
import sys

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

# Django REST Framework
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

# AnsibleWorks
from ansibleworks.main.access import *
from ansibleworks.main.base_views import *
from ansibleworks.main.models import *
from ansibleworks.main.rbac import *
from ansibleworks.main.serializers import *

def handle_error(request, status=404):
    context = {}
    print request.path, status
    if request.path.startswith('/admin/'):
        template_name = 'admin/%d.html' % status
    else:
        template_name = '%d.html' % status
    return render_to_response(template_name, context,
                              context_instance=RequestContext(request))

def handle_403(request):
    return handle_error(request, 403)

def handle_404(request):
    return handle_error(request, 404)

def handle_500(request):
    return handle_error(request, 500)

class ApiRootView(APIView):
    '''
    This resource is the root of the AnsibleWorks REST API and provides
    information about the available API versions.
    '''

    view_name = 'REST API'

    def get(self, request, format=None):
        ''' list supported API versions '''

        current = reverse('main:api_v1_root_view', args=[])
        data = dict(
           description = 'AnsibleWorks REST API',
           current_version = current,
           available_versions = dict(
              v1 = current
           )
        )
        return Response(data)

class ApiV1RootView(APIView):
    '''
    Version 1 of the REST API.

    Subject to change until the final 1.2 release.
    '''

    view_name = 'Version 1'

    def get(self, request, format=None):
        ''' list top level resources '''

        data = dict(
            organizations = reverse('main:organization_list'),
            users         = reverse('main:user_list'),
            projects      = reverse('main:project_list'),
            teams         = reverse('main:team_list'),
            credentials   = reverse('main:credential_list'),
            inventory     = reverse('main:inventory_list'),
            groups        = reverse('main:group_list'),
            hosts         = reverse('main:host_list'),
            job_templates = reverse('main:job_template_list'),
            jobs          = reverse('main:job_list'),
            authtoken     = reverse('main:auth_token_view'),
            me            = reverse('main:user_me_list'),
            config        = reverse('main:api_v1_config_view'),
        )
        return Response(data)

class ApiV1ConfigView(APIView):
    '''
    Various sitewide configuration settings (some may only be visible to
    superusers or organization admins):

    * `project_base_dir`: Path on the server where projects and playbooks are \
      stored.
    * `project_local_paths`: List of directories beneath `project_base_dir` to
      use when creating/editing a project.
    * `time_zone`: The configured time zone for the server.
    '''

    permission_classes = (IsAuthenticated,)
    view_name = 'Configuration'

    def get(self, request, format=None):
        '''Return various sitewide configuration settings.'''

        data = dict(
            time_zone = settings.TIME_ZONE,
        )
        if request.user.is_superuser or request.user.admin_of_organizations.filter(active=True).count():
            data.update(dict(
                project_base_dir = settings.PROJECTS_ROOT,
                project_local_paths = Project.get_local_path_choices(),
            ))
        return Response(data)

class AuthTokenView(ObtainAuthToken):
    '''
    POST username and password to this resource to obtain an authentication
    token for subsequent requests.
    
    Example JSON to post (application/json):

        {"username": "user", "password": "my pass"}

    Example form data to post (application/x-www-form-urlencoded):

        username=user&password=my%20pass

    If the username and password are valid, the response should be:

        {"token": "8f17825cf08a7efea124f2638f3896f6637f8745"}

    Otherwise, the response will indicate the error that occurred.

    For subsequent requests, pass the token via the HTTP request headers:

        Authenticate: Token 8f17825cf08a7efea124f2638f3896f6637f8745
    '''

    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

class OrganizationList(BaseList):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    # I can see the organizations if:
    #   I am a superuser
    #   I am an admin of the organization
    #   I am a member of the organization

    def get_queryset(self):
        ''' I can see organizations when I am a superuser, or I am an admin or user in that organization '''
        base = Organization.objects
        if self.request.user.is_superuser:
            return base.all()
        return base.filter(
            admins__in = [ self.request.user ]
        ).distinct() | base.filter(
            users__in = [ self.request.user ]
        ).distinct()

class OrganizationDetail(BaseDetail):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)

class OrganizationInventoriesList(BaseSubList):

    model = Inventory
    serializer_class = InventorySerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization
    relationship = 'inventories'
    postable = False

    def get_queryset(self):
        ''' to list inventories in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not (self.request.user.is_superuser or self.request.user in organization.admins.all()):
            # FIXME: use: organization.can_user_administrate(...) ?
            raise PermissionDenied()
        return Inventory.objects.filter(organization__in=[organization])

class OrganizationUsersList(BaseSubList):

    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization
    relationship = 'users'
    postable = True
    inject_primary_key_on_post_as = 'organization'
    filter_fields = ('username',)

    def get_queryset(self):
        ''' to list users in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not self.request.user.is_superuser and not self.request.user in organization.admins.all():
            raise PermissionDenied()
        return User.objects.filter(organizations__in = [ organization ])

class OrganizationAdminsList(BaseSubList):

    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization
    relationship = 'admins'
    postable = True
    inject_primary_key_on_post_as = 'organization'
    filter_fields = ('username',)

    def get_queryset(self):
        ''' to list admins in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not self.request.user.is_superuser and not self.request.user in organization.admins.all():
            raise PermissionDenied()
        return User.objects.filter(admin_of_organizations__in = [ organization ])

class OrganizationProjectsList(BaseSubList):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization  # for sub list
    relationship = 'projects'    # " "
    postable = True
    inject_primary_key_on_post_as = 'organization'
    filter_fields = ('name',)

    def get_queryset(self):
        ''' to list projects in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not (self.request.user.is_superuser or self.request.user in organization.admins.all()):
            raise PermissionDenied()
        return Project.objects.filter(organizations__in = [ organization ])

class OrganizationTeamsList(BaseSubList):

    model = Team
    serializer_class = TeamSerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization
    relationship = 'teams'
    postable = True
    inject_primary_key_on_post_as = 'organization'
    severable = False
    filter_fields = ('name',)

    def get_queryset(self):
        ''' to list users in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not self.request.user.is_superuser and not self.request.user in organization.admins.all():
            raise PermissionDenied()
        return Team.objects.filter(organization = organization)

class TeamList(BaseList):

    model = Team
    serializer_class = TeamSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    # I can see a team if:
    #   I am a superuser
    #   I am an admin of the organization that the team is
    #   I am on that team

    def get_queryset(self):
        ''' I can see organizations when I am a superuser, or I am an admin or user in that organization '''
        base = Team.objects
        if self.request.user.is_superuser:
            return base.all()
        return base.filter(
            organization__admins__in = [ self.request.user ]
        ).distinct() | base.filter(
            users__in = [ self.request.user ]
        ).distinct()

class TeamDetail(BaseDetail):

    model = Team
    serializer_class = TeamSerializer
    permission_classes = (CustomRbac,)

class TeamUsersList(BaseSubList):

    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)
    parent_model = Team
    relationship = 'users'
    postable = True
    inject_primary_key_on_post_as = 'team'
    severable = True
    filter_fields = ('username',)

    def get_queryset(self):
        # FIXME: audit all BaseSubLists to check for permissions on the original object too
        'team members can see the whole team, as can org admins or superusers'
        team = Team.objects.get(pk=self.kwargs['pk'])
        base = team.users.all()
        if self.request.user.is_superuser or self.request.user in team.organization.admins.all():
            return base
        if self.request.user in team.users.all():
            return base
        raise PermissionDenied()

class TeamPermissionsList(BaseSubList):

    model = Permission
    serializer_class = PermissionSerializer
    permission_classes = (CustomRbac,)
    parent_model = Team
    relationship = 'permissions'
    postable = True
    filter_fields = ('name',)
    inject_primary_key_on_post_as = 'team'

    def get_queryset(self):
        team = Team.objects.get(pk=self.kwargs['pk'])
        base = Permission.objects.filter(team = team)
        #if Team.can_user_administrate(self.request.user, team, None):
        if check_user_access(self.request.user, Team, 'change', team, None):
            return base
        elif team.users.filter(pk=self.request.user.pk).count() > 0:
            return base
        raise PermissionDenied()


class TeamProjectsList(BaseSubList):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)
    parent_model = Team
    relationship = 'projects'
    postable = True
    inject_primary_key_on_post_as = 'team'
    severable = True

    # FIXME: filter_fields is no longer used, think we can remove these references everywhere given new custom filtering -- MPD
    filter_fields = ('name',)

    def get_queryset(self):
        team = Team.objects.get(pk=self.kwargs['pk'])
        base = team.projects.all()
        if self.request.user.is_superuser or self.request.user in team.organization.admins.all():
            return base
        if self.request.user in team.users.all():
            return base
        raise PermissionDenied()


class TeamCredentialsList(BaseSubList):

    model = Credential
    serializer_class = CredentialSerializer
    permission_classes = (CustomRbac,)
    parent_model = Team
    relationship = 'credentials'
    postable = True
    inject_primary_key_on_post_as = 'team'
    filter_fields = ('name',)

    def get_queryset(self):
        team = Team.objects.get(pk=self.kwargs['pk'])
        #if not Team.can_user_administrate(self.request.user, team, None):
        if not check_user_access(self.request.user, Team, 'change', team, None):
            if not (self.request.user.is_superuser or self.request.user in team.users.all()):
                raise PermissionDenied()
        project_credentials = Credential.objects.filter(
            team = team
        )
        return project_credentials.distinct()


class ProjectList(BaseList):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    # I can see a project if
    #   I am a superuser
    #   I am an admin of the organization that contains the project
    #   I am a member of a team that also contains the project

    def get_queryset(self):
        ''' I can see organizations when I am a superuser, or I am an admin or user in that organization '''
        base = Project.objects
        if self.request.user.is_superuser:
            return base.all()
        my_teams = Team.objects.filter(users__in = [ self.request.user])
        my_orgs  = Organization.objects.filter(admins__in = [ self.request.user ])
        return base.filter(
            teams__in = my_teams
        ).distinct() | base.filter(
            organizations__in = my_orgs
        ).distinct()

class ProjectDetail(BaseDetail):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)

class ProjectDetailPlaybooks(generics.RetrieveAPIView):

    model = Project
    serializer_class = ProjectPlaybooksSerializer
    permission_classes = (CustomRbac,)

class ProjectOrganizationsList(BaseSubList):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)
    parent_model = Project
    relationship = 'organizations'
    postable = False
    filter_fields = ('name',)

    def get_queryset(self):
        project = Project.objects.get(pk=self.kwargs['pk'])
        if not self.request.user.is_superuser:
            raise PermissionDenied()
        return Organization.objects.filter(projects__in = [ project ])

class UserList(BaseList):

    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('username',)

    def post(self, request, *args, **kwargs):
        password = request.DATA.get('password', None)
        result = super(UserList, self).post(request, *args, **kwargs)
        if password:
            pk = result.data['id']
            user = User.objects.get(pk=pk)
            user.set_password(password)
            user.save()
        return result

    def get_queryset(self):
        ''' I can see user records when I'm a superuser, I'm that user, I'm their org admin, or I'm on a team with that user '''
        base = User.objects
        if self.request.user.is_superuser:
            return base.all()
        mine = base.filter(pk = self.request.user.pk).distinct()
        admin_of = base.filter(organizations__in = self.request.user.admin_of_organizations.all()).distinct()
        same_team = base.filter(teams__in = self.request.user.teams.all()).distinct()
        return mine | admin_of | same_team

class UserMeList(BaseList):

    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('username',)

    view_name = 'Me!'

    def post(self, request, *args, **kwargs):
        raise PermissionDenied()

    def get_queryset(self):
        ''' a quick way to find my user record '''
        return User.objects.filter(pk=self.request.user.pk)

class UserTeamsList(BaseSubList):

    model = Team
    serializer_class = TeamSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'teams'
    postable = False
    filter_fields = ('name',)

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        #if not UserHelper.can_user_administrate(self.request.user, user, None):
        if not check_user_access(self.request.user, User, 'change', user, None):
            raise PermissionDenied()
        return Team.objects.filter(users__in = [ user ])

class UserPermissionsList(BaseSubList):

    model = Permission
    serializer_class = PermissionSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'permissions'
    postable = True
    filter_fields = ('name',)
    inject_primary_key_on_post_as = 'user'

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        #if not UserHelper.can_user_administrate(self.request.user, user, None):
        if not check_user_access(self.request.user, User, 'change', user, None):
            raise PermissionDenied()
        return Permission.objects.filter(user=user)

class UserProjectsList(BaseSubList):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'teams'
    postable = False
    filter_fields = ('name',)

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        #if not UserHelper.can_user_administrate(self.request.user, user, None):
        if not check_user_access(self.request.user, User, 'change', user, None):
            raise PermissionDenied()
        teams = user.teams.all()
        return Project.objects.filter(teams__in = teams)

class UserCredentialsList(BaseSubList):

    model = Credential
    serializer_class = CredentialSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'credentials'
    postable = True
    inject_primary_key_on_post_as = 'user'
    filter_fields = ('name',)

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        #if not UserHelper.can_user_administrate(self.request.user, user, None):
        if not check_user_access(self.request.user, User, 'change', user, None):
            raise PermissionDenied()
        project_credentials = Credential.objects.filter(
            team__users__in = [ user ]
        )
        return user.credentials.distinct() | project_credentials.distinct()

class UserOrganizationsList(BaseSubList):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'organizations'
    postable = False
    filter_fields = ('name',)

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        #if not UserHelper.can_user_administrate(self.request.user, user, None):
        if not check_user_access(self.request.user, User, 'change', user, None):
            raise PermissionDenied()
        return Organization.objects.filter(users__in = [ user ])

class UserAdminOfOrganizationsList(BaseSubList):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'admin_of_organizations'
    postable = False
    filter_fields = ('name',)

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        #if not UserHelper.can_user_administrate(self.request.user, user, None):
        if not check_user_access(self.request.user, User, 'change', user, None):
            raise PermissionDenied()
        return Organization.objects.filter(admins__in = [ user ])

class UserDetail(BaseDetail):

    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)

    def put_filter(self, request, *args, **kwargs):
        ''' make sure non-read-only fields that can only be edited by admins, are only edited by admins '''
        obj = User.objects.get(pk=kwargs['pk'])
        if EditHelper.illegal_changes(request, obj, UserHelper):
            raise PermissionDenied()
        if 'password' in request.DATA:
            obj.set_password(request.DATA['password'])
            obj.save()
            request.DATA.pop('password')

class CredentialList(BaseList):

    model = Credential
    serializer_class = CredentialSerializer
    permission_classes = (CustomRbac,)
    postable = False

    def get_queryset(self):
        return get_user_queryset(self.request.user, self.model)

class CredentialDetail(BaseDetail):

    model = Credential
    serializer_class = CredentialSerializer
    permission_classes = (CustomRbac,)

class PermissionDetail(BaseDetail):

    model = Permission
    serializer_class = PermissionSerializer
    permission_classes = (CustomRbac,)

class InventoryList(BaseList):

    model = Inventory
    serializer_class = InventorySerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    def _filter_queryset(self, base):
        if self.request.user.is_superuser:
            return base.all()
        admin_of  = base.filter(organization__admins__in = [ self.request.user ]).distinct()
        has_user_perms = base.filter(
            permissions__user__in = [ self.request.user ],
            permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        has_team_perms = base.filter(
            permissions__team__in = self.request.user.teams.all(),
            permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        return admin_of | has_user_perms | has_team_perms

    def get_queryset(self):
        ''' I can see inventory when I'm a superuser, an org admin of the inventory, or I have permissions on it '''
        base = Inventory.objects
        return self._filter_queryset(base)

class InventoryDetail(BaseDetail):

    model = Inventory
    serializer_class = InventorySerializer
    permission_classes = (CustomRbac,)

class HostList(BaseList):

    model = Host
    serializer_class = HostSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    def get_queryset(self):
        '''
        I can see hosts when:
           I'm a superuser,
           or an organization admin of an inventory they are in
           or when I have allowing read permissions via a user or team on an inventory they are in
        '''
        base = Host.objects
        if self.request.user.is_superuser:
            return base.all()
        admin_of  = base.filter(inventory__organization__admins__in = [ self.request.user ]).distinct()
        has_user_perms = base.filter(
            inventory__permissions__user__in = [ self.request.user ],
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        has_team_perms = base.filter(
            inventory__permissions__team__in = self.request.user.teams.all(),
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        return admin_of | has_user_perms | has_team_perms

class HostDetail(BaseDetail):

    model = Host
    serializer_class = HostSerializer
    permission_classes = (CustomRbac,)

class InventoryHostsList(BaseSubList):

    model = Host
    serializer_class = HostSerializer
    permission_classes = (CustomRbac,)
    # to allow the sub-aspect listing
    parent_model = Inventory
    relationship = 'hosts'
    # to allow posting to this resource to create resources
    postable = True
    # FIXME: go back and add these to other SubLists
    inject_primary_key_on_post_as = 'inventory'
    severable = False
    filter_fields = ('name',)

    def get_queryset(self):
        inventory = Inventory.objects.get(pk=self.kwargs['pk'])
        base = inventory.hosts
        # FIXME: verify that you can can_read permission on the inventory is required
        return base.all()

class HostGroupsList(BaseSubList):
    ''' the list of groups a host is directly a member of '''

    model = Group
    serializer_class = GroupSerializer
    permission_classes = (CustomRbac,)
    parent_model = Host
    relationship = 'groups'
    postable = True
    inject_primary_key_on_post_as = 'host'
    filter_fields = ('name',)

    def get_queryset(self):

        parent = Host.objects.get(pk=self.kwargs['pk'])

        # FIXME: verify read permissions on this object are still required at a higher level

        base = parent.groups
        if self.request.user.is_superuser:
            return base.all()
        admin_of  = base.filter(inventory__organization__admins__in = [ self.request.user ]).distinct()
        has_user_perms = base.filter(
            inventory__permissions__user__in = [ self.request.user ],
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        has_team_perms = base.filter(
            inventory__permissions__team__in = self.request.user.teams.all(),
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        return admin_of | has_user_perms | has_team_perms

class HostAllGroupsList(BaseSubList):
    ''' the list of all groups of which the host is directly or indirectly a member '''

    model = Group
    serializer_class = GroupSerializer
    permission_classes = (CustomRbac,)
    parent_model = Host
    relationship = 'groups'
    filter_fields = ('name',)

    def get_queryset(self):

        parent = Host.objects.get(pk=self.kwargs['pk'])

        # FIXME: verify read permissions on this object are still required at a higher level

        base = parent.all_groups

        if self.request.user.is_superuser:
            return base.all()

        admin_of  = base.filter(inventory__organization__admins__in = [ self.request.user ]).distinct()
        has_user_perms = base.filter(
            inventory__permissions__user__in = [ self.request.user ],
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        has_team_perms = base.filter(
            inventory__permissions__team__in = self.request.user.teams.all(),
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        return admin_of | has_user_perms | has_team_perms

class GroupList(BaseList):

    model = Group
    serializer_class = GroupSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    def get_queryset(self):
        '''
        I can see groups  when:
           I'm a superuser,
           or an organization admin of an inventory they are in
           or when I have allowing read permissions via a user or team on an inventory they are in
        '''
        base = Group.objects
        if self.request.user.is_superuser:
            return base.all()
        admin_of  = base.filter(inventory__organization__admins__in = [ self.request.user ]).distinct()
        has_user_perms = base.filter(
            inventory__permissions__user__in = [ self.request.user ],
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        has_team_perms = base.filter(
            inventory__permissions__team__in = self.request.user.teams.all(),
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        return admin_of | has_user_perms | has_team_perms

class GroupChildrenList(BaseSubList):

    model = Group
    serializer_class = GroupSerializer
    permission_classes = (CustomRbac,)
    parent_model = Group
    relationship = 'children'
    postable = True
    inject_primary_key_on_post_as = 'parent'
    filter_fields = ('name',)

    def get_queryset(self):

        # FIXME: this is the mostly the same as GroupsList, share code similar to how done with Host and Group objects.

        parent = Group.objects.get(pk=self.kwargs['pk'])

        # FIXME: verify read permissions on this object are still required at a higher level

        base = parent.children
        if self.request.user.is_superuser:
            return base.all()
        admin_of  = base.filter(inventory__organization__admins__in = [ self.request.user ]).distinct()
        has_user_perms = base.filter(
            inventory__permissions__user__in = [ self.request.user ],
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        has_team_perms = base.filter(
            inventory__permissions__team__in = self.request.user.teams.all(),
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        return admin_of | has_user_perms | has_team_perms

class GroupHostsList(BaseSubList):
    ''' the list of hosts directly below a group '''

    model = Host
    serializer_class = HostSerializer
    permission_classes = (CustomRbac,)
    parent_model = Group
    relationship = 'hosts'
    postable = True
    inject_primary_key_on_post_as = 'group'
    filter_fields = ('name',)

    def get_queryset(self):

        parent = Group.objects.get(pk=self.kwargs['pk'])

        # FIXME: verify read permissions on this object are still required at a higher level

        base = parent.hosts
        if self.request.user.is_superuser:
            return base.all()
        admin_of  = base.filter(inventory__organization__admins__in = [ self.request.user ]).distinct()
        has_user_perms = base.filter(
            inventory__permissions__user__in = [ self.request.user ],
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        has_team_perms = base.filter(
            inventory__permissions__team__in = self.request.user.teams.all(),
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        return admin_of | has_user_perms | has_team_perms


class GroupAllHostsList(BaseSubList):
    ''' the list of all hosts below a group, even including subgroups '''

    model = Host
    serializer_class = HostSerializer
    permission_classes = (CustomRbac,)
    parent_model = Group
    relationship = 'hosts'
    filter_fields = ('name',)

    def get_queryset(self):

        parent = Group.objects.get(pk=self.kwargs['pk'])

        # FIXME: verify read permissions on this object are still required at a higher level

        base = parent.all_hosts

        if self.request.user.is_superuser:
            return base.all()

        admin_of  = base.filter(inventory__organization__admins__in = [ self.request.user ]).distinct()
        has_user_perms = base.filter(
            inventory__permissions__user__in = [ self.request.user ],
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        has_team_perms = base.filter(
            inventory__permissions__team__in = self.request.user.teams.all(),
            inventory__permissions__permission_type__in = PERMISSION_TYPES_ALLOWING_INVENTORY_READ,
        ).distinct()
        return admin_of | has_user_perms | has_team_perms


class GroupDetail(BaseDetail):

    model = Group
    serializer_class = GroupSerializer
    permission_classes = (CustomRbac,)

class InventoryGroupsList(BaseSubList):

    model = Group
    serializer_class = GroupSerializer
    permission_classes = (CustomRbac,)
    # to allow the sub-aspect listing
    parent_model = Inventory
    relationship = 'groups'
    # to allow posting to this resource to create resources
    postable = True
    # FIXME: go back and add these to other SubLists
    inject_primary_key_on_post_as = 'inventory'
    severable = False
    filter_fields = ('name',)

    def get_queryset(self):
        # FIXME: share code with inventory filter queryset methods (make that a classmethod)
        inventory = Inventory.objects.get(pk=self.kwargs['pk'])
        base = inventory.groups
        # FIXME: verify that you can can_read permission on the inventory is required
        return base

class InventoryRootGroupsList(BaseSubList):

    model = Group
    serializer_class = GroupSerializer
    permission_classes = (CustomRbac,)
    parent_model = Inventory
    relationship = 'groups'
    postable = True
    inject_primary_key_on_post_as = 'inventory'
    severable = False
    filter_fields = ('name',)

    def get_queryset(self):
        inventory = Inventory.objects.get(pk=self.kwargs['pk'])
        base = inventory.groups
        all_ids = base.values_list('id', flat=True)
        return base.exclude(parents__pk__in = all_ids)

class InventoryVariableDetail(BaseDetail):

    model = Inventory
    serializer_class = InventoryVariableDataSerializer
    permission_classes = (CustomRbac,)
    is_variable_data = True # Special flag for RBAC

class HostVariableDetail(BaseDetail):

    model = Host
    serializer_class = HostVariableDataSerializer
    permission_classes = (CustomRbac,)
    is_variable_data = True # Special flag for RBAC

class GroupVariableDetail(BaseDetail):

    model = Group
    serializer_class = GroupVariableDataSerializer
    permission_classes = (CustomRbac,)
    is_variable_data = True # Special flag for RBAC

class JobTemplateList(BaseList):

    model = JobTemplate
    serializer_class = JobTemplateSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    def get_queryset(self):
        return get_user_queryset(self.request.user, self.model)

class JobTemplateDetail(BaseDetail):

    model = JobTemplate
    serializer_class = JobTemplateSerializer
    permission_classes = (CustomRbac,)

class JobTemplateJobsList(BaseSubList):

    model = Job
    serializer_class = JobSerializer
    permission_classes = (CustomRbac,)
    # to allow the sub-aspect listing
    parent_model = JobTemplate
    relationship = 'jobs'
    # to allow posting to this resource to create resources
    postable = True
    # FIXME: go back and add these to other SubLists
    inject_primary_key_on_post_as = 'job_template'
    severable = False
    #filter_fields = ('name',)

    def get_queryset(self):
        # FIXME: Verify read permission on the job template.
        job_template = get_object_or_404(JobTemplate, pk=self.kwargs['pk'])
        return job_template.jobs

class JobList(BaseList):

    model = Job
    serializer_class = JobSerializer
    permission_classes = (CustomRbac,)

    def get_queryset(self):
        return self.model.objects.all() # FIXME

class JobDetail(BaseDetail):

    model = Job
    serializer_class = JobSerializer
    permission_classes = (CustomRbac,)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        # Only allow changes (PUT/PATCH) when job status is "new".
        if obj.status != 'new':
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super(JobDetail, self).update(request, *args, **kwargs)

class JobStart(generics.RetrieveAPIView):

    model = Job
    permission_classes = (CustomRbac,)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        data = dict(
            can_start=obj.can_start,
        )
        if obj.can_start:
            data['passwords_needed_to_start'] = obj.get_passwords_needed_to_start()
        return Response(data)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_start:
            result = obj.start(**request.DATA)
            if not result:
                data = dict(passwords_needed_to_start=obj.get_passwords_needed_to_start())
                return Response(data, status=400)
            else:
                return Response(status=202)
        else:
            return Response(status=405)

class JobCancel(generics.RetrieveAPIView):

    model = Job
    permission_classes = (CustomRbac,)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        data = dict(
            can_cancel=obj.can_cancel,
        )
        return Response(data)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            result = obj.cancel()
            return Response(status=202)
        else:
            return Response(status=405)

class BaseJobHostSummariesList(generics.ListAPIView):

    model = JobHostSummary
    serializer_class = JobHostSummarySerializer
    permission_classes = (CustomRbac,)
    parent_model = None # Subclasses must define this attribute.
    relationship = 'job_host_summaries'

    view_name = 'Job Host Summary List'

    def get_queryset(self):
        # FIXME: Verify read permission on the parent object and job.
        parent_obj = get_object_or_404(self.parent_model, pk=self.kwargs['pk'])
        return getattr(parent_obj, self.relationship)

class HostJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Host

class GroupJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Group

class JobJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Job

# FIXME: Subclasses of XJobHostSummaryList for failed/successful/etc.

class JobHostSummaryDetail(generics.RetrieveAPIView):

    model = JobHostSummary
    serializer_class = JobHostSummarySerializer
    permission_classes = (CustomRbac,)

class JobEventList(BaseList):

    model = JobEvent
    serializer_class = JobEventSerializer
    permission_classes = (CustomRbac,)

    def get_queryset(self):
        return self.model.objects.distinct() # FIXME: Permissions?

class JobEventDetail(generics.RetrieveAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer
    permission_classes = (CustomRbac,)

class JobEventChildrenList(generics.ListAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer
    permission_classes = (CustomRbac,)
    parent_model = JobEvent
    relationship = 'children'

    view_name = 'Job Event Children List'

    def get_queryset(self):
        # FIXME: Verify read permission on the parent object and job.
        parent_obj = get_object_or_404(self.parent_model, pk=self.kwargs['pk'])
        return getattr(parent_obj, self.relationship)

class JobEventHostsList(generics.ListAPIView):

    model = Host
    serializer_class = HostSerializer
    permission_classes = (CustomRbac,)
    parent_model = JobEvent
    relationship = 'hosts'

    view_name = 'Job Event Hosts List'

    def get_queryset(self):
        # FIXME: Verify read permission on the parent object and job.
        parent_obj = get_object_or_404(self.parent_model, pk=self.kwargs['pk'])
        return getattr(parent_obj, self.relationship)

class BaseJobEventsList(generics.ListAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer
    permission_classes = (CustomRbac,)
    parent_model = None # Subclasses must define this attribute.
    relationship = 'job_events'

    def get_queryset(self):
        # FIXME: Verify read permission on the parent object and job.
        parent_obj = get_object_or_404(self.parent_model, pk=self.kwargs['pk'])
        return getattr(parent_obj, self.relationship).distinct()

class HostJobEventsList(BaseJobEventsList):

    parent_model = Host

class GroupJobEventsList(BaseJobEventsList):

    parent_model = Group

class JobJobEventsList(BaseJobEventsList):

    parent_model = Job

# Create view functions for all of the class-based views to simplify inclusion
# in URL patterns and reverse URL lookups, converting CamelCase names to
# lowercase_with_underscore (e.g. MyView.as_view() becomes my_view).
this_module = sys.modules[__name__]
camelcase_to_underscore = lambda str: re.sub(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', str).lower().strip('_')
for attr, value in locals().items():
    if isinstance(value, type) and issubclass(value, APIView):
        name = camelcase_to_underscore(attr)
        view = value.as_view()
        setattr(this_module, name, view)
