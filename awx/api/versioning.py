# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

from rest_framework.reverse import reverse as drf_reverse
from rest_framework.versioning import URLPathVersioning as BaseVersioning


def reverse(viewname, args=None, kwargs=None, request=None, format=None, **extra):
    if request is None or getattr(request, 'version', None) is None:
        # We need the "current request" to determine the correct version to
        # prepend to reverse URLs.  If there is no "current request", assume
        # the latest API version.
        if kwargs is None:
            kwargs = {}
        if 'version' not in kwargs:
            kwargs['version'] = 'v2'
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
