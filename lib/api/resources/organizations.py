# myapp/api.py

from tastypie.resources import ModelResource
from tastypie.authentication import BasicAuthentication
from lib.api.auth import AcomAuthorization

import lib.main.models as models

class Organizations(ModelResource):

    class Meta:
        queryset = models.Organization.objects.all()
        resource_name = 'organizations'
        authentication = BasicAuthentication()
        authorization = AcomAuthorization()


