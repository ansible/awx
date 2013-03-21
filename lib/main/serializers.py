from django.contrib.auth.models import User as DjangoUser
from lib.main.models import User, Organization, Project
from rest_framework import serializers, pagination
from django.core.urlresolvers import reverse
import lib.urls

class OrganizationSerializer(serializers.ModelSerializer):

    # add the URL and related resources
    url           = serializers.CharField(source='get_absolute_url', read_only=True)
    related       = serializers.SerializerMethodField('get_related')

    # make certain fields read only
    creation_date = serializers.DateTimeField(read_only=True)
    active        = serializers.BooleanField(read_only=True)

    class Meta:

        model = Organization
        
        # whitelist the fields we want to show
        fields = ('url', 'id', 'name', 'description', 'creation_date', 'related')

    def get_related(self, obj):
        ''' related resource URLs '''

        return dict(
            audit_trail = reverse(lib.urls.views_OrganizationsAuditTrailList, args=(obj.pk,)),
            projects    = reverse(lib.urls.views_OrganizationsProjectsList,   args=(obj.pk,)),
            users       = reverse(lib.urls.views_OrganizationsUsersList,      args=(obj.pk,)),
            admins      = reverse(lib.urls.views_OrganizationsAdminsList,     args=(obj.pk,)),
            tags        = reverse(lib.urls.views_OrganizationsTagsList,       args=(obj.pk,))
        ) 





