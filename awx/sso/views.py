# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import urllib
import logging

# Django
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic import View
from django.views.generic.base import RedirectView
from django.utils.encoding import smart_text
from django.contrib import auth

# Django REST Framework
from rest_framework.renderers import JSONRenderer

# AWX
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
            auth.login(self.request, self.request.user)
            logger.info(smart_text(u"User {} logged in".format(self.request.user.username)))
            # TODO: remove these 2 cookie-sets after UI removes them
            response.set_cookie('userLoggedIn', 'true')
            current_user = UserSerializer(self.request.user)
            current_user = JSONRenderer().render(current_user.data)
            current_user = urllib.quote('%s' % current_user, '')
            response.set_cookie('current_user', current_user)
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
