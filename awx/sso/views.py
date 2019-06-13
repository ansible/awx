# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import urllib.parse
import logging

# Django
from django.urls import reverse
from django.http import HttpResponse
from django.views.generic import View
from django.views.generic.base import RedirectView
from django.utils.encoding import smart_text
from awx.api.serializers import UserSerializer
from rest_framework.renderers import JSONRenderer
from django.conf import settings

logger = logging.getLogger('awx.sso.views')


class BaseRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        last_path = self.request.COOKIES.get('lastPath', '')
        last_path = urllib.parse.quote(urllib.parse.unquote(last_path).strip('"'))
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
        if self.request.user and self.request.user.is_authenticated:
            logger.info(smart_text(u"User {} logged in".format(self.request.user.username)))
            response.set_cookie('userLoggedIn', 'true')
            current_user = UserSerializer(self.request.user)
            current_user = smart_text(JSONRenderer().render(current_user.data))
            current_user = urllib.parse.quote('%s' % current_user, '')
            response.set_cookie('current_user', current_user, secure=settings.SESSION_COOKIE_SECURE or None)
        return response


sso_complete = CompleteView.as_view()


class MetadataView(View):

    def get(self, request, *args, **kwargs):
        from social_django.utils import load_backend, load_strategy
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
