# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import urllib.parse

# Six

# Django
from django.conf import settings
from django.utils.functional import LazyObject
from django.shortcuts import redirect

# Python Social Auth
from social_core.exceptions import SocialAuthBaseException
from social_core.utils import social_logger
from social_django import utils
from social_django.middleware import SocialAuthExceptionMiddleware


class SocialAuthMiddleware(SocialAuthExceptionMiddleware):

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if request.path.startswith('/sso/login/'):
            request.session['social_auth_last_backend'] = callback_kwargs['backend']

    def process_request(self, request):
        if request.path.startswith('/sso'):
            # django-social keeps a list of backends in memory that it gathers
            # based on the value of settings.AUTHENTICATION_BACKENDS *at import
            # time*:
            # https://github.com/python-social-auth/social-app-django/blob/c1e2795b00b753d58a81fa6a0261d8dae1d9c73d/social_django/utils.py#L13
            #
            # our settings.AUTHENTICATION_BACKENDS can *change*
            # dynamically as Tower settings are changed (i.e., if somebody
            # configures Github OAuth2 integration), so we need to
            # _overwrite_ this in-memory value at the top of every request so
            # that we have the latest version
            # see: https://github.com/ansible/tower/issues/1979
            utils.BACKENDS = settings.AUTHENTICATION_BACKENDS
        token_key = request.COOKIES.get('token', '')
        token_key = urllib.parse.quote(urllib.parse.unquote(token_key).strip('"'))

        if not hasattr(request, 'successful_authenticator'):
            request.successful_authenticator = None

        if not request.path.startswith('/sso/') and 'migrations_notran' not in request.path:
            if request.user and request.user.is_authenticated():
                # The rest of the code base rely hevily on type/inheritance checks,
                # LazyObject sent from Django auth middleware can be buggy if not
                # converted back to its original object.
                if isinstance(request.user, LazyObject) and request.user._wrapped:
                    request.user = request.user._wrapped
                request.session.pop('social_auth_error', None)
                request.session.pop('social_auth_last_backend', None)

    def process_exception(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        if strategy is None or self.raise_exception(request, exception):
            return

        if isinstance(exception, SocialAuthBaseException) or request.path.startswith('/sso/'):
            backend = getattr(request, 'backend', None)
            backend_name = getattr(backend, 'name', 'unknown-backend')

            message = self.get_message(request, exception)
            if request.session.get('social_auth_last_backend') != backend_name:
                backend_name = request.session.get('social_auth_last_backend')
                message = request.GET.get('error_description', message)

            full_backend_name = backend_name
            try:
                idp_name = strategy.request_data()['RelayState']
                full_backend_name = '%s:%s' % (backend_name, idp_name)
            except KeyError:
                pass

            social_logger.error(message)

            url = self.get_redirect_uri(request, exception)
            request.session['social_auth_error'] = (full_backend_name, message)
            return redirect(url)

    def get_message(self, request, exception):
        msg = str(exception)
        if msg and msg[-1] not in '.?!':
            msg = msg + '.'
        return msg

    def get_redirect_uri(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        return strategy.session_get('next', '') or strategy.setting('LOGIN_ERROR_URL')
