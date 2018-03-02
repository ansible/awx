# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import logging
from awx import __version__ as tower_version

# Prepare the AWX environment.
from awx import prepare_env, MODE
prepare_env()


from django.core.handlers.base import BaseHandler  # NOQA
from django.core.wsgi import get_wsgi_application  # NOQA
import django  # NOQA
from django.conf import settings  # NOQA
from django.urls import resolve  # NOQA


"""
WSGI config for AWX project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

if MODE == 'production':
    logger = logging.getLogger('awx.main.models.jobs')
    try:
        fd = open("/var/lib/awx/.tower_version", "r")
        if fd.read().strip() != tower_version:
            raise Exception()
    except Exception:
        logger.error("Missing or incorrect metadata for Tower version.  Ensure Tower was installed using the setup playbook.")
        raise Exception("Missing or incorrect metadata for Tower version.  Ensure Tower was installed using the setup playbook.")


if django.__version__ != '1.11.7':
    raise RuntimeError("Django version other than 1.11.7 detected {}. \
            Monkey Patch to support short-circuit Django Middelware \
            is known to work for Django 1.11.7 and may not work with other, \
            even minor, versions.".format(django.__version__))


if settings.MIDDLEWARE:
    raise RuntimeError("MIDDLEWARE setting detected. \
            The 'migration in progress' view feature short-circuits OLD Django \
            MIDDLEWARE_CLASSES behavior. With the new Django MIDDLEWARE beahvior \
            it's possible to short-ciruit the middleware onion through supported \
            middleware mechanisms. The monkey patch wrapper below should be removed.")


def _wrapper_legacy_get_response(self, request):
    # short-circuit middleware
    if getattr(resolve(request.path), 'url_name', '') == 'migrations_notran':
        return self._get_response(request)
    # fall through to middle-ware
    else:
        return self._real_legacy_get_response(request)


BaseHandler._real_legacy_get_response = BaseHandler._legacy_get_response
BaseHandler._legacy_get_response = _wrapper_legacy_get_response

# Return the default Django WSGI application.
application = get_wsgi_application()
