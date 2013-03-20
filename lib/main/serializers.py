from django.contrib.auth.models import User as DjangoUser
from lib.main.models import User, Organization, Project
from rest_framework import serializers, pagination

class OrganizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = ('name', 'description')

