# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from oauth2_provider.urls import base_urlpatterns

from awx.api.views import (
    ApiOAuthAuthorizationRootView,
)


urls = [
    url(r'^$', ApiOAuthAuthorizationRootView.as_view(), name='oauth_authorization_root_view'),
] + base_urlpatterns


__all__ = ['urls']
