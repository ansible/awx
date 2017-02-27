# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import urllib
import logging

# Django
from django.conf import settings
from django.utils.timezone import now as tz_now
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import HTTP_HEADER_ENCODING

# AWX
from awx.main.models import UnifiedJob, AuthToken

logger = logging.getLogger('awx.api.authentication')


class TokenAuthentication(authentication.TokenAuthentication):
    '''
    Custom token authentication using tokens that expire and are associated
    with parameters specific to the request.
    '''

    model = AuthToken

    @staticmethod
    def _get_x_auth_token_header(request):
        auth = request.META.get('HTTP_X_AUTH_TOKEN', '')
        if isinstance(auth, type('')):
            # Work around django test client oddness
            auth = auth.encode(HTTP_HEADER_ENCODING)
        return auth

    @staticmethod
    def _get_auth_token_cookie(request):
        token = request.COOKIES.get('token', '')
        if token:
            token = urllib.unquote(token).strip('"')
            return 'token %s' % token
        return ''

    def authenticate(self, request):
        self.request = request

        # Prefer the custom X-Auth-Token header over the Authorization header,
        # to handle cases where the browser submits saved Basic auth and
        # overrides the UI's normal use of the Authorization header.
        auth = TokenAuthentication._get_x_auth_token_header(request).split()
        if not auth or auth[0].lower() != 'token':
            auth = authentication.get_authorization_header(request).split()
            # Prefer basic auth over cookie token
            if auth and auth[0].lower() == 'basic':
                return None
            elif not auth or auth[0].lower() != 'token':
                auth = TokenAuthentication._get_auth_token_cookie(request).split()
                if not auth or auth[0].lower() != 'token':
                    return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(auth[1])

    def authenticate_credentials(self, key):
        now = tz_now()
        # Retrieve the request hash and token.
        try:
            request_hash = self.model.get_request_hash(self.request)
            token = self.model.objects.select_related('user').get(
                key=key,
                request_hash=request_hash,
            )
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed(AuthToken.reason_long('invalid_token'))

        # Tell the user why their token was previously invalidated.
        if token.invalidated:
            raise exceptions.AuthenticationFailed(AuthToken.reason_long(token.reason))

        # Explicitly handle expired tokens
        if token.is_expired(now=now):
            token.invalidate(reason='timeout_reached')
            raise exceptions.AuthenticationFailed(AuthToken.reason_long('timeout_reached'))

        # Token invalidated due to session limit config being reduced
        # Session limit reached invalidation will also take place on authentication
        if settings.AUTH_TOKEN_PER_USER != -1:
            if not token.in_valid_tokens(now=now):
                token.invalidate(reason='limit_reached')
                raise exceptions.AuthenticationFailed(AuthToken.reason_long('limit_reached'))

        # If the user is inactive, then return an error.
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted'))

        # Refresh the token.
        # The token is extended from "right now" + configurable setting amount.
        token.refresh(now=now)

        # Return the user object and the token.
        return (token.user, token)


class TokenGetAuthentication(TokenAuthentication):

    def authenticate(self, request):
        if request.method.lower() == 'get':
            token = request.GET.get('token', None)
            if token:
                request.META['HTTP_X_AUTH_TOKEN'] = 'Token %s' % token
        return super(TokenGetAuthentication, self).authenticate(request)


class LoggedBasicAuthentication(authentication.BasicAuthentication):

    def authenticate(self, request):
        if not settings.AUTH_BASIC_ENABLED:
            return
        ret = super(LoggedBasicAuthentication, self).authenticate(request)
        if ret:
            username = ret[0].username if ret[0] else '<none>'
            logger.debug(smart_text(u"User {} performed a {} to {} through the API".format(username, request.method, request.path)))
        return ret

    def authenticate_header(self, request):
        if not settings.AUTH_BASIC_ENABLED:
            return
        return super(LoggedBasicAuthentication, self).authenticate_header(request)


class TaskAuthentication(authentication.BaseAuthentication):
    '''
    Custom authentication used for views accessed by the inventory and callback
    scripts when running a task.
    '''

    model = None

    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()
        if len(auth) != 2 or auth[0].lower() != 'token' or '-' not in auth[1]:
            return None
        pk, key = auth[1].split('-', 1)
        try:
            unified_job = UnifiedJob.objects.get(pk=pk, status='running')
        except UnifiedJob.DoesNotExist:
            return None
        token = unified_job.task_auth_token
        if auth[1] != token:
            raise exceptions.AuthenticationFailed(_('Invalid task token'))
        return (None, token)

    def authenticate_header(self, request):
        return 'Token'
