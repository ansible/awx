# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf import settings
from django.urls import re_path, include

from awx.main.views import handle_400, handle_403, handle_404, handle_500, handle_csp_violation, handle_login_redirect


urlpatterns = [
    re_path(r'', include('awx.ui.urls', namespace='ui')),
    re_path(r'^api/', include('awx.api.urls', namespace='api')),
    re_path(r'^sso/', include('awx.sso.urls', namespace='sso')),
    re_path(r'^sso/', include('social_django.urls', namespace='social')),
    re_path(r'^(?:api/)?400.html$', handle_400),
    re_path(r'^(?:api/)?403.html$', handle_403),
    re_path(r'^(?:api/)?404.html$', handle_404),
    re_path(r'^(?:api/)?500.html$', handle_500),
    re_path(r'^csp-violation/', handle_csp_violation),
    re_path(r'^login/', handle_login_redirect),
]

if settings.SETTINGS_MODULE == 'awx.settings.development':
    try:
        import debug_toolbar

        urlpatterns += [re_path(r'^__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass

handler400 = 'awx.main.views.handle_400'
handler403 = 'awx.main.views.handle_403'
handler404 = 'awx.main.views.handle_404'
handler500 = 'awx.main.views.handle_500'
