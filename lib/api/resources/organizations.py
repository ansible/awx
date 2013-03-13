# myapp/api.py
from tastypie.resources import ModelResource
import lib.main.models as models

class Organizations(ModelResource):

    class Meta:
        queryset = models.Organization.objects.all()
        resource_name = 'organizations'

