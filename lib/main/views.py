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
from rest_framework.settings import api_settings
from rest_framework.authtoken.views import ObtainAuthToken
import exceptions
import datetime
from base_views import *

class AuthTokenView(ObtainAuthToken):

    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    # FIXME: Show a better form for HTML view
    # FIXME: How to make this view discoverable?

class OrganizationsList(BaseList):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

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
    inject_primary_key_on_post_as = 'organization'
    filter_fields = ('username',)

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
    inject_primary_key_on_post_as = 'organization'
    filter_fields = ('username',)

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
    inject_primary_key_on_post_as = 'organization'
    filter_fields = ('name',)

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
    inject_primary_key_on_post_as = 'organization'
    filter_fields = ('name',)

    def _get_queryset(self):
        ''' to list tags in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not (self.request.user.is_superuser or self.request.user in organization.admins.all()):
            # FIXME: use: organization.can_user_administrate(self.request.user)
            raise PermissionDenied()
        return Tag.objects.filter(organization_by_tag__in = [ organization ])

class OrganizationsTeamsList(BaseSubList):

    model = Team
    serializer_class = TeamSerializer
    permission_classes = (CustomRbac,)
    parent_model = Organization
    relationship = 'teams'
    postable = True
    inject_primary_key_on_post_as = 'organization'
    severable = False
    filter_fields = ('name',)

    def _get_queryset(self):
        ''' to list users in the organization, I must be a superuser or org admin '''
        organization = Organization.objects.get(pk=self.kwargs['pk'])
        if not self.request.user.is_superuser and not self.request.user in organization.admins.all():
            raise PermissionDenied()
        return Team.objects.filter(organization = organization)

class TeamsList(BaseList):

    model = Team
    serializer_class = TeamSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    # I can see a team if:
    #   I am a superuser
    #   I am an admin of the organization that the team is
    #   I am on that team

    def _get_queryset(self):
        ''' I can see organizations when I am a superuser, or I am an admin or user in that organization '''
        base = Team.objects
        if self.request.user.is_superuser:
            return base.all()
        return base.filter(
            admins__in = [ self.request.user ]
        ).distinct() | base.filter(
            users__in = [ self.request.user ]
        ).distinct()

class TeamsDetail(BaseDetail):

    model = Team
    serializer_class = TeamSerializer
    permission_classes = (CustomRbac,)

class TeamsUsersList(BaseSubList):

    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)
    parent_model = Team
    relationship = 'users'
    postable = True
    inject_primary_key_on_post_as = 'team'
    severable = True
    filter_fields = ('username',)

    def _get_queryset(self):
        # FIXME: audit all BaseSubLists to check for permissions on the original object too
        'team members can see the whole team, as can org admins or superusers'
        team = Team.objects.get(pk=self.kwargs['pk'])
        base = team.users.all()
        if self.request.user.is_superuser or self.request.user in team.organization.admins.all():
            return base
        if self.request.user in team.users.all():
            return base
        raise PermissionDenied()

class TeamsCredentialsList(BaseSubList):

    model = Credential
    serializer_class = CredentialSerializer
    permission_classes = (CustomRbac,)
    parent_model = Team
    relationship = 'credentials'
    postable = True
    inject_primary_key_on_post_as = 'team'
    filter_fields = ('name',)

    def _get_queryset(self):
        team = Team.objects.get(pk=self.kwargs['pk'])
        if not Team.can_user_administrate(self.request.user, team):
            if not (self.request.user.is_superuser or self.request.user in team.users.all()):
                raise PermissionDenied()
        project_credentials = Credential.objects.filter(
            team = team
        )
        return project_credentials.distinct()


class ProjectsList(BaseList):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    # I can see a project if
    #   I am a superuser
    #   I am an admin of the organization that contains the project
    #   I am a member of a team that also contains the project

    def _get_queryset(self):
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

class ProjectsDetail(BaseDetail):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)

class ProjectsOrganizationsList(BaseSubList):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)
    parent_model = Project
    relationship = 'organizations'
    postable = False
    filter_fields = ('name',)

    def _get_queryset(self):
        project = Project.objects.get(pk=self.kwargs['pk'])
        if not self.request.user.is_superuser:
            raise PermissionDenied()
        return Organization.objects.filter(projects__in = [ project ])

class TagsDetail(BaseDetail):

    model = Tag
    serializer_class = TagSerializer
    permission_classes = (CustomRbac,)

class UsersList(BaseList):

    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('username',)

    def post(self, request, *args, **kwargs):
        password = request.DATA.get('password', None)
        result = super(UsersList, self).post(request, *args, **kwargs)
        if password:
            pk = result.data['id']
            user = User.objects.get(pk=pk)
            user.set_password(password)
            user.save()
        return result

    def _get_queryset(self):
        ''' I can see user records when I'm a superuser, I'm that user, I'm their org admin, or I'm on a team with that user '''
        base = User.objects
        if self.request.user.is_superuser:
            return base.all()
        mine = base.filter(pk = self.request.user.pk).distinct()
        admin_of = base.filter(organizations__in = self.request.user.admin_of_organizations.all()).distinct()
        same_team = base.filter(teams__in = self.request.user.teams.all()).distinct()
        return mine | admin_of | same_team

class UsersMeList(BaseList):

    model = User
    serializer_class = UserSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('username',)

    def post(self, request, *args, **kwargs):
        raise PermissionDenied()

    def _get_queryset(self):
        ''' a quick way to find my user record '''
        return User.objects.filter(pk=self.request.user.pk)

class UsersTeamsList(BaseSubList):

    model = Team
    serializer_class = TeamSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'teams'
    postable = False
    filter_fields = ('name',)

    def _get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        if not UserHelper.can_user_administrate(self.request.user, user):
            raise PermissionDenied()
        return Team.objects.filter(users__in = [ user ])

class UsersProjectsList(BaseSubList):

    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'teams'
    postable = False
    filter_fields = ('name',)

    def _get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        if not UserHelper.can_user_administrate(self.request.user, user):
            raise PermissionDenied()
        teams = user.teams.all()
        return Project.objects.filter(teams__in = teams)

class UsersCredentialsList(BaseSubList):

    model = Credential
    serializer_class = CredentialSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'credentials'
    postable = True
    inject_primary_key_on_post_as = 'user'
    filter_fields = ('name',)

    def _get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        if not UserHelper.can_user_administrate(self.request.user, user):
            raise PermissionDenied()
        project_credentials = Credential.objects.filter(
            team__users__in = [ user ]
        )
        return user.credentials.distinct() | project_credentials.distinct()

class UsersOrganizationsList(BaseSubList):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'organizations'
    postable = False
    filter_fields = ('name',)

    def _get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        if not UserHelper.can_user_administrate(self.request.user, user):
            raise PermissionDenied()
        return Organization.objects.filter(users__in = [ user ])

class UsersAdminOrganizationsList(BaseSubList):

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)
    parent_model = User
    relationship = 'admin_of_organizations'
    postable = False
    filter_fields = ('name',)

    def _get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        if not UserHelper.can_user_administrate(self.request.user, user):
            raise PermissionDenied()
        return Organization.objects.filter(admins__in = [ user ])

class UsersDetail(BaseDetail):

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

class CredentialsDetail(BaseDetail):

    model = Credential
    serializer_class = CredentialSerializer
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

    def _get_queryset(self):
        ''' I can see inventory when I'm a superuser, an org admin of the inventory, or I have permissions on it '''
        base = Inventory.objects
        return self._filter_queryset(base)

class InventoryDetail(BaseDetail):

    model = Inventory
    serializer_class = InventorySerializer
    permission_classes = (CustomRbac,)

class HostsList(BaseList):

    model = Host
    serializer_class = HostSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    def _get_queryset(self):
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

class HostsDetail(BaseDetail):

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

    def _get_queryset(self):
        inventory = Inventory.objects.get(pk=self.kwargs['pk'])
        base = inventory.hosts
        # FIXME: verify that you can can_read permission on the inventory is required
        return base.all()

class GroupsList(BaseList):

    model = Group
    serializer_class = GroupSerializer
    permission_classes = (CustomRbac,)
    filter_fields = ('name',)

    def _get_queryset(self):
        '''
        I can see groups  when:
           I'm a superuser,
           or an organization admin of an inventory they are in
           or when I have allowing read permissions via a user or team on an inventory they are in
        '''
        base = Groups.objects
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

class GroupsChildrenList(BaseSubList):

    model = Group
    serializer_class = GroupSerializer
    permission_classes = (CustomRbac,)
    parent_model = Group
    relationship = 'children'
    postable = True
    inject_primary_key_on_post_as = 'parent'
    filter_fields = ('name',)

    def _get_queryset(self):

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

class GroupsHostsList(BaseSubList):
    ''' the list of hosts directly below a group '''

    model = Host
    serializer_class = HostSerializer
    permission_classes = (CustomRbac,)
    parent_model = Group
    relationship = 'hosts'
    postable = True
    inject_primary_key_on_post_as = 'group'
    filter_fields = ('name',)

    def _get_queryset(self):

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


class GroupsAllHostsList(BaseSubList):
    ''' the list of all hosts below a group, even including subgroups '''

    model = Host
    serializer_class = HostSerializer
    permission_classes = (CustomRbac,)
    parent_model = Group
    relationship = 'hosts'
    filter_fields = ('name',)

    def _child_hosts(self, parent):
        # TODO: should probably be a method on the model
        result = parent.hosts.distinct()
        if parent.children.count() == 0:
            return result
        else:
            for child in parent.children.all():
                if child == parent:
                    # shouldn't happen, but be prepared in case DB is weird
                    continue
                result = result | self._child_hosts(child)
            return result

    def _get_queryset(self):

        parent = Group.objects.get(pk=self.kwargs['pk'])

        # FIXME: verify read permissions on this object are still required at a higher level

        base = self._child_hosts(parent)

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


class GroupsDetail(BaseDetail):

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

    def _get_queryset(self):
        # FIXME: share code with inventory filter queryset methods (make that a classmethod)
        inventory = Inventory.objects.get(pk=self.kwargs['pk'])
        base = inventory.groups
        # FIXME: verify that you can can_read permission on the inventory is required
        return base

class GroupsVariableDetail(VariableBaseDetail):

    model = VariableData
    serializer_class = VariableDataSerializer
    permission_classes = (CustomRbac,)
    parent_model = Group
    reverse_relationship = 'variable_data'
    relationship = 'group'

class HostsVariableDetail(VariableBaseDetail):

    model = VariableData
    serializer_class = VariableDataSerializer
    permission_classes = (CustomRbac,)
    parent_model = Host
    reverse_relationship = 'variable_data'
    relationship = 'host'

class VariableDetail(BaseDetail):

    model = VariableData
    serializer_class = VariableDataSerializer
    permission_classes = (CustomRbac,)

    def put(self, request, *args, **kwargs):
        raise PermissionDenied()



