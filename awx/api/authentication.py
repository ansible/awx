# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django REST Framework
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import HTTP_HEADER_ENCODING

# AWX
from awx.main.models import UnifiedJob, AuthToken


class TokenAuthentication(authentication.TokenAuthentication):
    '''
    Custom token authentication using tokens that expire and are associated
    with parameters specific to the request.
    '''

    model = AuthToken

    def _get_x_auth_token_header(self, request):
        auth = request.META.get('HTTP_X_AUTH_TOKEN', '')
        if isinstance(auth, type('')):
            # Work around django test client oddness
            auth = auth.encode(HTTP_HEADER_ENCODING)
        return auth

    def authenticate(self, request):
        self.request = request

        # Prefer the custom X-Auth-Token header over the Authorization header,
        # to handle cases where the browser submits saved Basic auth and
        # overrides the UI's normal use of the Authorization header.
        auth = self._get_x_auth_token_header(request).split()
        if not auth or auth[0].lower() != 'token':
            auth = authentication.get_authorization_header(request).split()
            if not auth or auth[0].lower() != 'token':
                return None

        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(auth[1])

    def authenticate_credentials(self, key):
        # Retrieve the request hash and token.
        try:
            request_hash = self.model.get_request_hash(self.request)
            token = self.model.objects.select_related('user').get(
                key=key,
                request_hash=request_hash,
            )
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        # Sanity check: Ensure that the token is still valid.
        # Tokens expire if they are not used for 30 minutes.
        if token.expired:
            raise exceptions.AuthenticationFailed('Token is expired')

        # Sanity check: If the user is inactive, then return an error.
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted')

        # Refresh the token.
        # This updates the time that the token was last used, meaning that
        # now the token is valid for 30 minutes from "right now".
        token.refresh()

        # Return the user object and the token.
        return (token.user, token)

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
            raise exceptions.AuthenticationFailed('Invalid task token')
        return (None, token)

    def authenticate_header(self, request):
        return 'Token'
