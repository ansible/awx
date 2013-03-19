from tastypie.resources import Resource, ModelResource, ALL
from tastypie.authentication import BasicAuthentication
from tastypie import fields, utils
from lib.api.auth import AcomAuthorization
#from django.conf.urls import url
import lib.main.models as models
from lib.vendor.extendedmodelresource import ExtendedModelResource
from tastypie.authorization import Authorization

class OrganizationAuthorization(Authorization):
    """
    Our Authorization class for UserResource and its nested.
    """

    def is_authorized(self, request, object=None):
        if request.user.username == 'admin':
            return True
        else:
            return False

    def is_authorized(self, request, object=None):
        # HACK
        if 'admin' in request.user.username:
            return True
        return False

    def apply_limits(self, request, object_list):
        return object_list.all()

    def is_authorized_nested_projects(self, request, parent_object, object=None):
        # Is request.user authorized to access the EntryResource as # nested?
        return True

    def apply_limits_nested_projects(self, request, parent_object, object_list):
        # Advanced filtering.
        # Note that object_list already only contains the objects that
        # are associated to parent_object.
        return object_list.all()

class Organizations(ExtendedModelResource):

    class Meta:
        # related fields...

        queryset = models.Organization.objects.all()
        resource_name = 'organizations'

        #authentication = BasicAuthentication()
        #authorization = AcomAuthorization()
        authorization = OrganizationAuthorization()
    
    class Nested:
        #users    = fields.ToManyField('lib.api.resources.Users', 'users', related_name='organizations', blank=True, help_text='list of all organization users')
        #admins   = fields.ToManyField('lib.api.resources.Users', 'admins', related_name='admin_of_organizations', blank=True, help_text='list of administrator users')
        projects = fields.ToManyField('lib.api.resources.Projects', 'projects') # blank=True, help_text='list of projects')

    def is_authorized(self, request, object=None):
        return True

class Users(ExtendedModelResource):

    class Meta:
        queryset = models.User.objects.all()
        resource_name = 'users'
        authorization = AcomAuthorization()

class Projects(ExtendedModelResource):


    class Meta:
        queryset = models.Project.objects.all()
        resource_name = 'projects'
        authorization = AcomAuthorization()

    #organizations = fields.ToManyField('lib.api.resources.Organizations', 'organizations', help_text='which organizations is this project in?')

        
