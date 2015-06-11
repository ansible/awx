# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url, patterns, include

handler403 = 'awx.main.views.handle_403'
handler404 = 'awx.main.views.handle_404'
handler500 = 'awx.main.views.handle_500'

urlpatterns = patterns('',
                       url(r'', include('awx.ui.urls', namespace='ui', app_name='ui')),
                       url(r'^api/', include('awx.api.urls', namespace='api', app_name='api')))

urlpatterns += patterns('awx.main.views',
                        url(r'^403.html$', 'handle_403'),
                        url(r'^404.html$', 'handle_404'),
                        url(r'^500.html$', 'handle_500'))
