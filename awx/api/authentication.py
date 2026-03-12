# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.conf import settings
from django.utils.encoding import smart_str

# Django REST Framework
from rest_framework import authentication

logger = logging.getLogger('awx.api.authentication')


class LoggedBasicAuthentication(authentication.BasicAuthentication):
    def authenticate(self, request):
        if not settings.AUTH_BASIC_ENABLED:
            return
        ret = super(LoggedBasicAuthentication, self).authenticate(request)
        if ret:
            username = ret[0].username if ret[0] else '<none>'
            logger.info(smart_str(u"User {} performed a {} to {} through the API".format(username, request.method, request.path)))
        return ret

    def authenticate_header(self, request):
        if not settings.AUTH_BASIC_ENABLED:
            return
        return super(LoggedBasicAuthentication, self).authenticate_header(request)


class SessionAuthentication(authentication.SessionAuthentication):
    def authenticate_header(self, request):
        return 'Session'
