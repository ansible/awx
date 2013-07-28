# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

"""
WSGI config for AWX project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

# Prepare the AWX environment.
from awx import prepare_env
prepare_env()

# Return the default Django WSGI application.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
