# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


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

        return dict(
            audit_trail = reverse(lib.urls.views_OrganizationsAuditTrailList, args=(obj.pk,)),
            projects    = reverse(lib.urls.views_OrganizationsProjectsList,   args=(obj.pk,)),
            users       = reverse(lib.urls.views_OrganizationsUsersList,      args=(obj.pk,)),
            admins      = reverse(lib.urls.views_OrganizationsAdminsList,     args=(obj.pk,)),
            tags        = reverse(lib.urls.views_OrganizationsTagsList,       args=(obj.pk,))
        ) 

class AuditTrailSerializer(BaseSerializer):
    
    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')
    
    class Meta:
        model = AuditTrail
        fields = ('url', 'id', 'modified_by', 'delta', 'detail', 'comment')

    def get_related(self, obj):
        return dict()

class ProjectSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Project
        fields = ('url', 'id', 'name', 'description', 'creation_date', 'local_repository', 'default_playbook', 'scm_type')

    def get_related(self, obj):
        # FIXME: add related resources: inventories
        return dict()


class InventorySerializer(BaseSerializer):
    
    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Inventory
        fields = ('url', 'id', 'name', 'description', 'creation_date', 'organization')

    def get_related(self, obj):
        # FIXME: add related resources: hosts, groups
        return dict()

class HostSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Host
        fields = ('url', 'id', 'name', 'description', 'creation_date', 'inventory')

    def get_related(self, obj):
        # FIXME: add related resources
        return dict()

class GroupSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Group
        fields = ('url', 'id', 'name', 'description', 'creation_date', 'inventory')

    def get_related(self, obj):
        # FIXME: add related resources
        return dict()

class TeamSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Team
        fields = ('url', 'id', 'related', 'name', 'description', 'creation_date')

    def get_related(self, obj):
        # FIXME: add related resources: projects, users, organizations
        return dict()


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
        return dict()

class VariableDataSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = VariableData
        fields = ('url', 'id', 'data', 'related', 'name', 'description', 'creation_date')

    def get_related(self, obj):
        # FIXME: related resources, maybe just the audit trail
        return dict()



