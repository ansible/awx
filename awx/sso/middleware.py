# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import urllib

# Six
import six

# Django
from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.utils.timezone import now

# Python Social Auth
from social.exceptions import SocialAuthBaseException
from social.utils import social_logger
from social.apps.django_app.middleware import SocialAuthExceptionMiddleware

# Ansible Tower
from awx.main.models import AuthToken


class SocialAuthMiddleware(SocialAuthExceptionMiddleware):

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if request.path.startswith('/sso/login/'):
            request.session['social_auth_last_backend'] = callback_kwargs['backend']

    def process_request(self, request):
        token_key = request.COOKIES.get('token', '')
        token_key = urllib.quote(urllib.unquote(token_key).strip('"'))

        if not hasattr(request, 'successful_authenticator'):
            request.successful_authenticator = None

        if not request.path.startswith('/sso/') and 'migrations_notran' not in request.path:

            # If token isn't present but we still have a user logged in via Django
            # sessions, log them out.
            if not token_key and request.user and request.user.is_authenticated():
                logout(request)

            # If a token is present, make sure it matches a valid one in the
            # database, and log the user via Django session if necessary.
            # Otherwise, log the user out via Django sessions.
            elif token_key:

                try:
                    auth_token = AuthToken.objects.filter(key=token_key, expires__gt=now())[0]
                except IndexError:
                    auth_token = None

                if not auth_token and request.user and request.user.is_authenticated():
                    logout(request)
                elif auth_token and request.user.is_anonymous is False and request.user != auth_token.user:
                    logout(request)
                    auth_token.user.backend = ''
                    login(request, auth_token.user)
                    auth_token.refresh()

                if auth_token and request.user and request.user.is_authenticated():
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
        msg = six.text_type(exception)
        if msg and msg[-1] not in '.?!':
            msg = msg + '.'
        return msg

    def get_redirect_uri(self, request, exception):
        strategy = getattr(request, 'social_strategy', None)
        return strategy.session_get('next', '') or strategy.setting('LOGIN_ERROR_URL')
