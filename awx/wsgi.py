# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

"""
WSGI config for AWX project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

import os
import sys
import warnings
from awx import MODE
from distutils.sysconfig import get_python_lib

# Update the default settings environment variable based on current mode.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'awx.settings.%s' % MODE)

# Add local site-packages directory to path.
local_site_packages = os.path.join(os.path.dirname(__file__), 'lib',
                                   'site-packages')
sys.path.insert(0, local_site_packages)

# Hide DeprecationWarnings when running in production.  Need to first load
# settings to apply our filter after Django's own warnings filter.
from django.conf import settings
if not settings.DEBUG:
    warnings.simplefilter('ignore', DeprecationWarning)

# Return the default Django WSGI application.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
