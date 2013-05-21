# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

from django.conf import settings
from django.conf.urls import *

urlpatterns = patterns('',
    url(r'', include('ansibleworks.ui.urls', namespace='ui', app_name='ui')),
    url(r'^api/', include('ansibleworks.main.urls', namespace='main', app_name='main')),
)

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    from django.contrib import admin
    admin.autodiscover()
    urlpatterns += patterns('',
        url(r'^admin/', include(admin.site.urls)),
    )
