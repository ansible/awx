# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Production settings for AWX project.
from defaults import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Clear database settings to force production environment to define them.
DATABASES = {}

# Enable South to look for migrations in .pyc files.
SOUTH_USE_PYC = True

# Clear the secret key to force production environment to define it.
SECRET_KEY = None

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Production should only use minified JS for UI.
USE_MINIFIED_JS = True 

# URL used by inventory script and callback plugin to access API.
INTERNAL_API_URL = 'http://127.0.0.1:80'

# Load remaining settings from the global settings file specified in the
# environment, defaulting to /etc/awx/settings.py.
settings_file = os.environ.get('AWX_SETTINGS_FILE',
                               '/etc/awx/settings.py')
try:
    execfile(settings_file)
except IOError, e:
    from django.core.exceptions import ImproperlyConfigured
    if not os.path.exists(settings_file):
        msg = 'No AWX configuration found at %s.' % settings_file
        if 'AWX_SETTINGS_FILE' not in os.environ:
            msg += '\nDefine the AWX_SETTINGS_FILE environment variable to '
            msg += 'specify an alternate path.'
    else:
        msg = 'Unable to load %s: %s' % (settings_file, str(e))
    raise ImproperlyConfigured(msg)
