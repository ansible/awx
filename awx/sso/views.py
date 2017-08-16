# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import urllib
import logging

# Django
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.timezone import now, utc
from django.views.generic import View
from django.views.generic.base import RedirectView
from django.utils.encoding import smart_text

# Django REST Framework
from rest_framework.renderers import JSONRenderer

# AWX
from awx.main.models import AuthToken
from awx.api.serializers import UserSerializer

logger = logging.getLogger('awx.sso.views')


class BaseRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        last_path = self.request.COOKIES.get('lastPath', '')
        last_path = urllib.quote(urllib.unquote(last_path).strip('"'))
        url = reverse('ui:index')
        if last_path:
            return '%s#%s' % (url, last_path)
        else:
            return url


sso_error = BaseRedirectView.as_view()
sso_inactive = BaseRedirectView.as_view()


class CompleteView(BaseRedirectView):

    def dispatch(self, request, *args, **kwargs):
        response = super(CompleteView, self).dispatch(request, *args, **kwargs)
        if self.request.user and self.request.user.is_authenticated():
            request_hash = AuthToken.get_request_hash(self.request)
            try:
                token = AuthToken.objects.filter(user=request.user,
                                                 request_hash=request_hash,
                                                 reason='',
                                                 expires__gt=now())[0]
                token.refresh()
                logger.info(smart_text(u"User {} logged in".format(self.request.user.username)))
            except IndexError:
                token = AuthToken.objects.create(user=request.user,
                                                 request_hash=request_hash)
                logger.info(smart_text(u"User {} logged in".format(self.request.user.username)))
            request.session['auth_token_key'] = token.key
            token_key = urllib.quote('"%s"' % token.key)
            response.set_cookie('token', token_key)
            token_expires = token.expires.astimezone(utc).strftime('%Y-%m-%dT%H:%M:%S')
            token_expires = '%s.%03dZ' % (token_expires, token.expires.microsecond / 1000)
            token_expires = urllib.quote('"%s"' % token_expires)
            response.set_cookie('token_expires', token_expires)
            response.set_cookie('userLoggedIn', 'true')
            current_user = UserSerializer(self.request.user)
            current_user = JSONRenderer().render(current_user.data)
            current_user = urllib.quote('%s' % current_user, '')
            response.set_cookie('current_user', current_user)
        return response


sso_complete = CompleteView.as_view()


class MetadataView(View):

    def get(self, request, *args, **kwargs):
        from social.apps.django_app.utils import load_backend, load_strategy
        complete_url = reverse('social:complete', args=('saml', ))
        saml_backend = load_backend(
            load_strategy(request),
            'saml',
            redirect_uri=complete_url,
        )
        try:
            metadata, errors = saml_backend.generate_metadata_xml()
        except Exception as e:
            logger.exception('unable to generate SAML metadata')
            errors = e
        if not errors:
            return HttpResponse(content=metadata, content_type='text/xml')
        else:
            return HttpResponse(content=str(errors), content_type='text/plain')


saml_metadata = MetadataView.as_view()
