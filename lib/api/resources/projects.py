# myapp/api.py

from tastypie.resources import ModelResource
from tastypie.authentication import BasicAuthentication
from lib.api.auth import AcomAuthorization
import lib.main.models as models

class Projects(ModelResource):

    class Meta:
        queryset = models.Project.objects.all()
        resource_name = 'projects'
        authentication = BasicAuthentication()
        authorization = AcomAuthorization()

        
