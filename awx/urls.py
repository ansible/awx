# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf import settings
from django.urls import re_path, include, path

from ansible_base.lib.dynamic_config.dynamic_urls import api_urls, api_version_urls, root_urls

from ansible_base.resource_registry.urls import urlpatterns as resource_api_urls

from awx.main.views import handle_400, handle_403, handle_404, handle_500, handle_csp_violation, handle_login_redirect


def get_urlpatterns(prefix=None):
    if not prefix:
        prefix = '/'
    else:
        prefix = f'/{prefix}/'

    urlpatterns = [
        path(f'api{prefix}', include('awx.api.urls', namespace='api')),
    ]

    urlpatterns += [
        path(f'api{prefix}v2/', include(resource_api_urls)),
        path(f'api{prefix}v2/', include(api_version_urls)),
        path(f'api{prefix}', include(api_urls)),
        path('', include(root_urls)),
        re_path(r'^(?:api/)?400.html$', handle_400),
        re_path(r'^(?:api/)?403.html$', handle_403),
        re_path(r'^(?:api/)?404.html$', handle_404),
        re_path(r'^(?:api/)?500.html$', handle_500),
        re_path(r'^csp-violation/', handle_csp_violation),
        re_path(r'^login/', handle_login_redirect),
        # want api/v2/doesnotexist to return a 404, not match the ui urls,
        # so use a negative lookahead assertion here
        re_path(r'^(?!api/).*', include('awx.ui.urls', namespace='ui')),
    ]

    if settings.DYNACONF.is_development_mode:
        try:
            import debug_toolbar

            urlpatterns += [re_path(r'^__debug__/', include(debug_toolbar.urls))]
        except ImportError:
            pass

    return urlpatterns


urlpatterns = get_urlpatterns()

handler400 = 'awx.main.views.handle_400'
handler403 = 'awx.main.views.handle_403'
handler404 = 'awx.main.views.handle_404'
handler500 = 'awx.main.views.handle_500'
