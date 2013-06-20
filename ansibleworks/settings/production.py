# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Production settings for Ansible Commander project.

from defaults import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Clear database settings to force production environment to define them.
DATABASES = {}

# Clear the secret key to force production environment to define it.
SECRET_KEY = None

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Production should only use minified JS for UI.
# CLH 6/20/13 - leave the following set to False until we actually have minified js ready
USE_MINIFIED_JS = False

INTERNAL_API_URL = 'http://127.0.0.1:80'

# If a local_settings.py file is present here, use it and ignore the global
# settings.  Normally, local settings would only be present during development.
try:
    local_settings_file = os.path.join(os.path.dirname(__file__),
                                       'local_settings.py')
    execfile(local_settings_file)
except IOError:
    # Otherwise, rely on the global settings file specified in the environment,
    # defaulting to /etc/ansibleworks/settings.py.
    settings_file = os.environ.get('ANSIBLEWORKS_SETTINGS_FILE',
                                   '/etc/ansibleworks/settings.py')
    try:
        execfile(settings_file)
    except IOError:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured('No AnsibleWorks configuration found in %s'\
                                   % settings_file)
