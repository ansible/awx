# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

from django.conf import settings

from rest_framework.reverse import reverse as drf_reverse
from rest_framework.versioning import URLPathVersioning as BaseVersioning


def get_request_version(request):
    """
    The API version of a request as an integer i.e., 1 or 2
    """
    version = settings.REST_FRAMEWORK['DEFAULT_VERSION']
    if request and hasattr(request, 'version'):
        version = request.version
        if version is None:
            # For requests to /api/
            return None
    return int(version.lstrip('v'))


def reverse(viewname, args=None, kwargs=None, request=None, format=None, **extra):
    if request is None or getattr(request, 'version', None) is None:
        # We need the "current request" to determine the correct version to
        # prepend to reverse URLs.  If there is no "current request", assume
        # the latest API version.
        if kwargs is None:
            kwargs = {}
        if 'version' not in kwargs:
            kwargs['version'] = settings.REST_FRAMEWORK['DEFAULT_VERSION']
    return drf_reverse(viewname, args, kwargs, request, format, **extra)


class URLPathVersioning(BaseVersioning):

    def reverse(self, viewname, args=None, kwargs=None, request=None, format=None, **extra):
        if request.version is not None:
            kwargs = {} if (kwargs is None) else kwargs
            kwargs[self.version_param] = request.version
        request = None

        return super(BaseVersioning, self).reverse(
            viewname, args, kwargs, request, format, **extra
        )
