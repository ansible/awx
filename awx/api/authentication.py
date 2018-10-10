# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.conf import settings
from django.utils.encoding import smart_text

# Django REST Framework
from rest_framework import authentication

# Django-OAuth-Toolkit
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

logger = logging.getLogger('awx.api.authentication')


class LoggedBasicAuthentication(authentication.BasicAuthentication):

    def authenticate(self, request):
        if not settings.AUTH_BASIC_ENABLED:
            return
        ret = super(LoggedBasicAuthentication, self).authenticate(request)
        if ret:
            username = ret[0].username if ret[0] else '<none>'
            logger.info(smart_text(u"User {} performed a {} to {} through the API".format(username, request.method, request.path)))
        return ret

    def authenticate_header(self, request):
        if not settings.AUTH_BASIC_ENABLED:
            return
        return super(LoggedBasicAuthentication, self).authenticate_header(request)


class SessionAuthentication(authentication.SessionAuthentication):
    
    def authenticate_header(self, request):
        return 'Session'


class LoggedOAuth2Authentication(OAuth2Authentication):

    def authenticate(self, request):
        ret = super(LoggedOAuth2Authentication, self).authenticate(request)
        if ret:
            user, token = ret
            username = user.username if user else '<none>'
            logger.info(smart_text(
                u"User {} performed a {} to {} through the API using OAuth 2 token {}.".format(
                    username, request.method, request.path, token.pk
                )
            ))
            setattr(user, 'oauth_scopes', [x for x in token.scope.split() if x])
        return ret
