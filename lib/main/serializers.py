from django.contrib.auth.models import User as DjangoUser
from lib.main.models import User, Organization, Project
from rest_framework import serializers, pagination

class OrganizationSerializer(serializers.ModelSerializer):

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Organization
        fields = ('url', 'id', 'name', 'description')
