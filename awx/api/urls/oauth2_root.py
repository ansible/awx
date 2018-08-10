# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from oauthlib import oauth2
from oauth2_provider import views

from awx.api.views import (
    ApiOAuthAuthorizationRootView,
)


class TokenView(views.TokenView):

    def create_token_response(self, request):
        try:
            return super(TokenView, self).create_token_response(request)
        except oauth2.AccessDeniedError as e:
            return request.build_absolute_uri(), {}, str(e), '403'


urls = [
    url(r'^$', ApiOAuthAuthorizationRootView.as_view(), name='oauth_authorization_root_view'),
    url(r"^authorize/$", views.AuthorizationView.as_view(), name="authorize"),
    url(r"^token/$", TokenView.as_view(), name="token"),
    url(r"^revoke_token/$", views.RevokeTokenView.as_view(), name="revoke-token"),
]


__all__ = ['urls']
