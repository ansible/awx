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

from django.contrib.auth.models import User
from lib.main.models import *
from rest_framework import serializers, pagination
from django.core.urlresolvers import reverse
from django.core.serializers import json
import lib.urls

class BaseSerializer(serializers.ModelSerializer):
    pass

class OrganizationSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    # make certain fields read only
    creation_date = serializers.DateTimeField(read_only=True) # FIXME: is model Date or DateTime, fix model
    active        = serializers.BooleanField(read_only=True)

    class Meta:
        model = Organization
        fields = ('url', 'id', 'name', 'description', 'creation_date', 'related') # whitelist

    def get_related(self, obj):
        ''' related resource URLs '''

        res = dict(
            audit_trail = reverse(lib.urls.views_OrganizationsAuditTrailList, args=(obj.pk,)),
            projects    = reverse(lib.urls.views_OrganizationsProjectsList,   args=(obj.pk,)),
            users       = reverse(lib.urls.views_OrganizationsUsersList,      args=(obj.pk,)),
            admins      = reverse(lib.urls.views_OrganizationsAdminsList,     args=(obj.pk,)),
            tags        = reverse(lib.urls.views_OrganizationsTagsList,       args=(obj.pk,)),
            teams       = reverse(lib.urls.views_OrganizationsTeamsList,      args=(obj.pk,)),
        )
        if obj.created_by:
            res['created_by']  = reverse(lib.urls.views_UsersDetail, args=(obj.created_by.pk,))

        return res

class AuditTrailSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = AuditTrail
        fields = ('url', 'id', 'modified_by', 'delta', 'detail', 'comment')

    def get_related(self, obj):
        res = dict()
        if obj.modified_by:
            res['modified_by']  = reverse(lib.urls.views_UsersDetail, args=(obj.modified_by.pk,))
        return res

class ProjectSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Project
        fields = ('url', 'id', 'name', 'description', 'creation_date', 'local_path')#, 'default_playbook', 'scm_type')

    def get_related(self, obj):
        res = dict(
            organizations = reverse(lib.urls.views_ProjectsOrganizationsList, args=(obj.pk,)),
        )
        if obj.created_by:
            res['created_by']  = reverse(lib.urls.views_UsersDetail, args=(obj.created_by.pk,))
        return res


class InventorySerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Inventory
        fields = ('url', 'id', 'name', 'description', 'creation_date', 'organization')

    def get_related(self, obj):
        res = dict(
            hosts        = reverse(lib.urls.views_HostsList,           args=(obj.pk,)),
            groups       = reverse(lib.urls.views_GroupsList,          args=(obj.pk,)),
            organization = reverse(lib.urls.views_OrganizationsDetail, args=(obj.organization.pk,)),
        )
        if obj.created_by:
            res['created_by']  = reverse(lib.urls.views_UsersDetail, args=(obj.created_by.pk,))
        return res

class HostSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Host
        fields = ('url', 'id', 'name', 'description', 'creation_date', 'inventory')

    def get_related(self, obj):
        res = dict(
            variable_data = reverse(lib.urls.views_HostsVariableDetail, args=(obj.pk,)),
            inventory     = reverse(lib.urls.views_InventoryDetail,     args=(obj.inventory.pk,)),
        )
        # NICE TO HAVE: possible reverse resource to show what groups the host is in
        if obj.created_by:
            res['created_by']  = reverse(lib.urls.views_UsersDetail, args=(obj.created_by.pk,))
        return res

class GroupSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Group
        fields = ('url', 'id', 'name', 'description', 'creation_date', 'inventory')

    def get_related(self, obj):
        res = dict(
            variable_data = reverse(lib.urls.views_GroupsVariableDetail, args=(obj.pk,)),
            hosts         = reverse(lib.urls.views_GroupsHostsList,      args=(obj.pk,)),
            children      = reverse(lib.urls.views_GroupsChildrenList,   args=(obj.pk,)),
            all_hosts     = reverse(lib.urls.views_GroupsAllHostsList,   args=(obj.pk,)),
            inventory     = reverse(lib.urls.views_InventoryDetail,      args=(obj.inventory.pk,)),
        )
        if obj.created_by:
            res['created_by']  = reverse(lib.urls.views_UsersDetail, args=(obj.created_by.pk,))
        return res

class TeamSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Team
        fields = ('url', 'id', 'related', 'name', 'description', 'organization', 'creation_date')

    # FIXME: TODO: include related collections but also related FK urls

    def get_related(self, obj):
        res = dict(
            projects     = reverse(lib.urls.views_TeamsProjectsList,     args=(obj.pk,)),
            users        = reverse(lib.urls.views_TeamsUsersList,        args=(obj.pk,)),
            credentials  = reverse(lib.urls.views_TeamsCredentialsList,  args=(obj.pk,)),
            organization = reverse(lib.urls.views_OrganizationsDetail,   args=(obj.pk,)),
        )
        if obj.created_by:
            res['created_by']  = reverse(lib.urls.views_UsersDetail, args=(obj.created_by.pk,))
        return res

class CredentialSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    # FIXME: may want to make soem of these filtered based on user accessing
    class Meta:
        model = Credential
        fields = (
            'url', 'id', 'related', 'name', 'description', 'creation_date',
            'default_username', 'ssh_key_data', 'ssh_key_unlock', 'ssh_password', 'sudo_password',
            'user', 'team'
        )

    def get_related(self, obj):
        # FIXME: no related collections, do want to add user and team if defined
        res = dict(
        )
        if obj.created_by:
            res['created_by']  = reverse(lib.urls.views_UsersDetail, args=(obj.created_by.pk,))
        return res

    def validate(self, attrs):
        ''' some fields cannot be changed once written '''
        if self.object is not None:
            # this is an update
            if self.object.user != attrs['user']:
                raise serializers.ValidationError("user cannot be changed")
            if self.object.team != attrs['team']:
                raise serializers.ValidationError("team cannot be changed")
        return attrs

class UserSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.SerializerMethodField('get_absolute_url_override')
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'is_superuser', 'related')

    def get_related(self, obj):
        return dict(
            teams                  = reverse(lib.urls.views_UsersTeamsList,              args=(obj.pk,)),
            organizations          = reverse(lib.urls.views_UsersOrganizationsList,      args=(obj.pk,)),
            admin_of_organizations = reverse(lib.urls.views_UsersAdminOrganizationsList, args=(obj.pk,)),
        )

    def get_absolute_url_override(self, obj):
        import lib.urls
        return reverse(lib.urls.views_UsersDetail, args=(obj.pk,))


class TagSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Tag
        fields = ('url', 'id', 'name')

    def get_related(self, obj):
        res = dict()
        return res

class VariableDataSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = VariableData
        fields = ('url', 'id', 'data', 'related', 'name', 'description', 'creation_date')

    def get_related(self, obj):
        # FIXME: add host or group if defined
        res = dict(
        )
        if obj.created_by:
            res['created_by']  = reverse(lib.urls.views_UsersDetail, args=(obj.created_by.pk,))
        return res

class JobTemplateSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = JobTemplate
        fields = ('url', 'id', 'related', 'name', 'description', 'job_type', 'credential', 'project', 'inventory', 'created_by', 'creation_date')

    def get_related(self, obj):
        # FIXME: fill in once further defined.  related resources, credential, project, inventory, etc
        res = dict(
        )
        if obj.created_by:
            res['created_by']  = reverse(lib.urls.views_UsersDetail, args=(obj.created_by.pk,))
        return res
    

