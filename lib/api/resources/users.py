# myapp/api.py

from tastypie.resources import ModelResource
from tastypie.authentication import BasicAuthentication
from lib.api.auth import AcomAuthorization
import lib.main.models as models

class Users(ModelResource):

    class Meta:
        queryset = models.User.objects.all()
        resource_name = 'users'
        authentication = BasicAuthentication()
        authorization = AcomAuthorization()

        
