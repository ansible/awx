# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import re
import logging
from collections import OrderedDict

# Django
from django.conf import settings
from django.utils.encoding import smart_text, force_text
from django.utils.timezone import now
from django.views.decorators.cache import never_cache


# Django REST Framework
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

# Python Social Auth
from social_core.backends.utils import load_backends

# AWX
from awx.main.models import AuthToken
from awx.api.generics import APIView
from awx.api.serializers import AuthTokenSerializer

from awx.conf.license import feature_enabled, feature_exists

from awx.main.consumers import emit_channel_notification

logger = logging.getLogger('awx.api.views')


class AuthView(APIView):

    authentication_classes = []
    permission_classes = (AllowAny,)
    new_in_240 = True

    def get(self, request):
        from rest_framework.reverse import reverse
        data = OrderedDict()
        err_backend, err_message = request.session.get('social_auth_error', (None, None))
        auth_backends = load_backends(settings.AUTHENTICATION_BACKENDS, force_load=True).items()
        # Return auth backends in consistent order: Google, GitHub, SAML.
        auth_backends.sort(key=lambda x: 'g' if x[0] == 'google-oauth2' else x[0])
        for name, backend in auth_backends:
            if (not feature_exists('enterprise_auth') and
                not feature_enabled('ldap')) or \
                (not feature_enabled('enterprise_auth') and
                 name in ['saml', 'radius']):
                    continue

            login_url = reverse('social:begin', args=(name,))
            complete_url = request.build_absolute_uri(reverse('social:complete', args=(name,)))
            backend_data = {
                'login_url': login_url,
                'complete_url': complete_url,
            }
            if name == 'saml':
                backend_data['metadata_url'] = reverse('sso:saml_metadata')
                for idp in sorted(settings.SOCIAL_AUTH_SAML_ENABLED_IDPS.keys()):
                    saml_backend_data = dict(backend_data.items())
                    saml_backend_data['login_url'] = '%s?idp=%s' % (login_url, idp)
                    full_backend_name = '%s:%s' % (name, idp)
                    if (err_backend == full_backend_name or err_backend == name) and err_message:
                        saml_backend_data['error'] = err_message
                    data[full_backend_name] = saml_backend_data
            else:
                if err_backend == name and err_message:
                    backend_data['error'] = err_message
                data[name] = backend_data
        return Response(data)


class AuthTokenView(APIView):

    authentication_classes = []
    permission_classes = (AllowAny,)
    serializer_class = AuthTokenSerializer
    model = AuthToken

    def get_serializer(self, *args, **kwargs):
        serializer = self.serializer_class(*args, **kwargs)
        # Override when called from browsable API to generate raw data form;
        # update serializer "validated" data to be displayed by the raw data
        # form.
        if hasattr(self, '_raw_data_form_marker'):
            # Always remove read only fields from serializer.
            for name, field in serializer.fields.items():
                if getattr(field, 'read_only', None):
                    del serializer.fields[name]
            serializer._data = self.update_raw_data(serializer.data)
        return serializer

    @never_cache
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            request_hash = AuthToken.get_request_hash(self.request)
            try:
                token = AuthToken.objects.filter(user=serializer.validated_data['user'],
                                                 request_hash=request_hash,
                                                 expires__gt=now(),
                                                 reason='')[0]
                token.refresh()
                if 'username' in request.data:
                    logger.info(smart_text(u"User {} logged in".format(request.data['username'])),
                                extra=dict(actor=request.data['username']))
            except IndexError:
                token = AuthToken.objects.create(user=serializer.validated_data['user'],
                                                 request_hash=request_hash)
                if 'username' in request.data:
                    logger.info(smart_text(u"User {} logged in".format(request.data['username'])),
                                extra=dict(actor=request.data['username']))
                # Get user un-expired tokens that are not invalidated that are
                # over the configured limit.
                # Mark them as invalid and inform the user
                invalid_tokens = AuthToken.get_tokens_over_limit(serializer.validated_data['user'])
                for t in invalid_tokens:
                    emit_channel_notification('control-limit_reached', dict(group_name='control',
                                                                            reason=force_text(AuthToken.reason_long('limit_reached')),
                                                                            token_key=t.key))
                    t.invalidate(reason='limit_reached')

            # Note: This header is normally added in the middleware whenever an
            # auth token is included in the request header.
            headers = {
                'Auth-Token-Timeout': int(settings.AUTH_TOKEN_EXPIRATION),
                'Pragma': 'no-cache',
            }
            return Response({'token': token.key, 'expires': token.expires}, headers=headers)
        if 'username' in request.data:
            logger.warning(smart_text(u"Login failed for user {}".format(request.data['username'])),
                           extra=dict(actor=request.data['username']))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if 'HTTP_AUTHORIZATION' in request.META:
            token_match = re.match("Token\s(.+)", request.META['HTTP_AUTHORIZATION'])
            if token_match:
                filter_tokens = AuthToken.objects.filter(key=token_match.groups()[0])
                if filter_tokens.exists():
                    filter_tokens[0].invalidate()
        return Response(status=status.HTTP_204_NO_CONTENT)
