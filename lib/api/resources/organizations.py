# myapp/api.py

from tastypie.resources import ModelResource
from lib.api.auth import AcomAuthentication, AcomAuthorization

import lib.main.models as models

class Organizations(ModelResource):

    class Meta:
        queryset = models.Organization.objects.all()
        resource_name = 'organizations'
        authentication = AcomAuthentication()
        authorization = AcomAuthorization()


