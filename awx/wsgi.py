# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import logging
from awx import __version__ as tower_version

# Prepare the AWX environment.
from awx import prepare_env, MODE
prepare_env()


from django.core.wsgi import WSGIHandler  # NOQA
import django  # NOQA
from django.conf import settings  # NOQA
from django.urls import resolve  # NOQA
import social_django  # NOQA


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

if social_django.__version__ != '2.1.0':
    raise RuntimeError("social_django version other than 2.1.0 detected {}. \
            Confirm that per-request social_django.utils.BACKENDS override \
            still works".format(social_django.__version__))


if django.__version__ != '1.11.20':
    raise RuntimeError("Django version other than 1.11.20 detected {}. \
            Inherit from WSGIHandler to support short-circuit Django Middleware. \
            This is known to work for Django 1.11.20 and may not work with other, \
            even minor, versions.".format(django.__version__))


if settings.MIDDLEWARE:
    raise RuntimeError("MIDDLEWARE setting detected. \
            The 'migration in progress' view feature short-circuits OLD Django \
            MIDDLEWARE_CLASSES behavior. With the new Django MIDDLEWARE beahvior \
            it's possible to short-ciruit the middleware onion through supported \
            middleware mechanisms. Further, from django.core.wsgi.get_wsgi_application() \
            should be called to get an instance of WSGIHandler().")


class AWXWSGIHandler(WSGIHandler):
    def _legacy_get_response(self, request):
        try:
            # resolve can raise a 404, in that case, pass through to the
            # "normal" middleware
            if getattr(resolve(request.path), 'url_name', '') == 'migrations_notran':
                # short-circuit middleware
                request._cors_enabled = False
                return self._get_response(request)
        except django.urls.Resolver404:
            pass
        # fall through to middle-ware
        return super(AWXWSGIHandler, self)._legacy_get_response(request)


# Return the default Django WSGI application.
def get_wsgi_application():
    django.setup(set_prefix=False)
    return AWXWSGIHandler()


application = get_wsgi_application()
