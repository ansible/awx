from django.conf import settings
from django.conf.urls import *
from tastypie.api import Api
from lib.api.resources import Organizations

v1_api = Api(api_name='v1')
v1_api.register(Organizations())


urlpatterns = patterns('',
   (r'', include(v1_api.urls)),
)
