# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

from django.conf import settings
from django.urls import NoReverseMatch

from rest_framework.reverse import _reverse
from rest_framework.versioning import URLPathVersioning as BaseVersioning


def drf_reverse(viewname, args=None, kwargs=None, request=None, format=None, **extra):
    """
    Copy and monkey-patch `rest_framework.reverse.reverse` to prevent adding unwarranted
    query string parameters.
    """
    scheme = getattr(request, 'versioning_scheme', None)
    if scheme is not None:
        try:
            url = scheme.reverse(viewname, args, kwargs, request, format, **extra)
        except NoReverseMatch:
            # In case the versioning scheme reversal fails, fallback to the
            # default implementation
            url = _reverse(viewname, args, kwargs, request, format, **extra)
    else:
        url = _reverse(viewname, args, kwargs, request, format, **extra)

    return url


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
