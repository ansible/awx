# myapp/api.py

from tastypie.resources import ModelResource
from tastypie.authentication import BasicAuthentication
from tastypie import fields #, utils

from lib.api.auth import AcomAuthorization
from lib.api.resources.projects import Projects
from lib.api.resources.users import Users

import lib.main.models as models

class Organizations(ModelResource):

    users    = fields.ToManyField(Users, 'users')
    admins   = fields.ToManyField(Users, 'admins')
    projects = fields.ToManyField(Projects, 'projects')

    class Meta:
        queryset = models.Organization.objects.all()
        resource_name = 'organizations'
        authentication = BasicAuthentication()
        authorization = AcomAuthorization()

        
