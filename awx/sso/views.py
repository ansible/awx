# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import urllib.parse
import logging

# Django
from django.urls import reverse
from django.views.generic.base import RedirectView
from django.utils.encoding import smart_str
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
            logger.info(smart_str(u"User {} logged in".format(self.request.user.username)))
            response.set_cookie(
                'userLoggedIn', 'true', secure=getattr(settings, 'SESSION_COOKIE_SECURE', False), samesite=getattr(settings, 'USER_COOKIE_SAMESITE', 'Lax')
            )
            response.setdefault('X-API-Session-Cookie-Name', getattr(settings, 'SESSION_COOKIE_NAME', 'awx_sessionid'))
        return response


sso_complete = CompleteView.as_view()
