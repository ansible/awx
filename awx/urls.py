# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url, include
from django.conf import settings
from awx.main.views import (
    handle_400,
    handle_403,
    handle_404,
    handle_500,
    handle_csp_violation,
    handle_login_redirect,
)


urlpatterns = [
    url(r'', include('awx.ui_next.urls', namespace='ui_next')),
    url(r'', include('awx.ui.urls', namespace='ui')),
    url(r'^api/', include('awx.api.urls', namespace='api')),
    url(r'^sso/', include('awx.sso.urls', namespace='sso')),
    url(r'^sso/', include('social_django.urls', namespace='social')),
    url(r'^(?:api/)?400.html$', handle_400),
    url(r'^(?:api/)?403.html$', handle_403),
    url(r'^(?:api/)?404.html$', handle_404),
    url(r'^(?:api/)?500.html$', handle_500),
    url(r'^csp-violation/', handle_csp_violation),
    url(r'^login/', handle_login_redirect),
]

if settings.SETTINGS_MODULE == 'awx.settings.development':
    try:
        import debug_toolbar
        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls))
        ]
    except ImportError:
        pass

handler400 = 'awx.main.views.handle_400'
handler403 = 'awx.main.views.handle_403'
handler404 = 'awx.main.views.handle_404'
handler500 = 'awx.main.views.handle_500'
