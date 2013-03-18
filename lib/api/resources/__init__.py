from tastypie.resources import ModelResource, ALL
from tastypie.authentication import BasicAuthentication
from tastypie import fields, utils
from lib.api.auth import AcomAuthorization
#from django.conf.urls import url
import lib.main.models as models

class Organizations(ModelResource):

    class Meta:
        # related fields...
        queryset = models.Organization.objects.all()
        resource_name = 'organizations'
        authentication = BasicAuthentication()
        authorization = AcomAuthorization()
        #filtering = {
        #   'projects': ALL
        #}
 
    users    = fields.ToManyField('lib.api.resources.Users', 'users', related_name='organizations', blank=True, help_text='list of all organization users')
    admins   = fields.ToManyField('lib.api.resources.Users', 'admins', related_name='admin_of_organizations', blank=True, help_text='list of administrator users')
    projects = fields.ToManyField('lib.api.resources.Projects', 'projects', related_name='organizations', blank=True, help_text='list of projects')

class Users(ModelResource):

    class Meta:
        queryset = models.User.objects.all()
        resource_name = 'users'
        authentication = BasicAuthentication()
        authorization = AcomAuthorization()

class Projects(ModelResource):


    class Meta:
        queryset = models.Project.objects.all()
        resource_name = 'projects'
        authentication = BasicAuthentication()
        authorization = AcomAuthorization()

    organizations = fields.ToManyField('lib.api.resources.Organizations', 'organizations', help_text='which organizations is this project in?')
        
