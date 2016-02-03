# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url, patterns, include

handler400 = 'awx.main.views.handle_400'
handler403 = 'awx.main.views.handle_403'
handler404 = 'awx.main.views.handle_404'
handler500 = 'awx.main.views.handle_500'

urlpatterns = patterns(
    '',
    url(r'', include('awx.ui.urls', namespace='ui', app_name='ui')),
    url(r'^api/', include('awx.api.urls', namespace='api', app_name='api')),
    url(r'^sso/', include('awx.sso.urls', namespace='sso', app_name='sso')),
    url(r'^sso/', include('social.apps.django_app.urls', namespace='social')),
)

urlpatterns += patterns(
    'awx.main.views',
    url(r'^(?:api/)?400.html$', 'handle_400'),
    url(r'^(?:api/)?403.html$', 'handle_403'),
    url(r'^(?:api/)?404.html$', 'handle_404'),
    url(r'^(?:api/)?500.html$', 'handle_500'),
)
