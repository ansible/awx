from django.contrib.auth.models import User
from lib.main.models import *
from rest_framework import serializers, pagination
from django.core.urlresolvers import reverse
import lib.urls

class BaseSerializer(serializers.ModelSerializer):
    pass

class OrganizationSerializer(BaseSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    # make certain fields read only
    creation_date = serializers.DateTimeField(read_only=True)
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

class UserSerializer(BaseSerializer):
   
    # FIXME: *** this is really about exposing the Django auth_user via REST so it may require
    # some custom save hooks in the view.
 
    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')
    
    class Meta:
        model = User
        # FIXME: make sure is_active is and is_superuser is read only
        fields = ('url', 'id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'is_superuser')

    def get_related(self, obj):
        # FIXME: add related lookups?
        return dict()

class TagSerializer(BaseSerializer):
    
    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    class Meta:
        model = Tag
        fields = ('url', 'id', 'name')

    def get_related(self, obj):
        return dict()



