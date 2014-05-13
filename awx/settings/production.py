# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Production settings for AWX project.

# Python
import sys
import traceback

# Django Split Settings
from split_settings.tools import optional, include

# Load default settings.
from defaults import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG
SQL_DEBUG = DEBUG

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

# Absolute filesystem path to the directory for job status stdout
# This directory should not be web-accessible
JOBOUTPUT_ROOT = '/var/lib/awx/job_status/'

# The heartbeat file for the tower scheduler
SCHEDULE_METADATA_LOCATION = '/var/lib/awx/.tower_cycle'

LOGGING['handlers']['rotating_file'] = {
    'level': 'WARNING',
    'class':'logging.handlers.RotatingFileHandler',
    'filters': ['require_debug_false'],
    'filename': '/var/log/awx/tower_warnings.log',
    'maxBytes': 1024*1024*5, # 5 MB
    'backupCount': 5,
    'formatter':'simple',
}

# Load settings from any .py files in the global conf.d directory specified in
# the environment, defaulting to /etc/awx/conf.d/.
settings_dir = os.environ.get('AWX_SETTINGS_DIR', '/etc/awx/conf.d/')
settings_files = os.path.join(settings_dir, '*.py')

# Load remaining settings from the global settings file specified in the
# environment, defaulting to /etc/awx/settings.py.
settings_file = os.environ.get('AWX_SETTINGS_FILE',
                               '/etc/awx/settings.py')

# Attempt to load settings from /etc/awx/settings.py first, followed by
# /etc/awx/conf.d/*.py.
try:
    include(
        settings_file,
        optional(settings_files),
        scope=locals(),
    )
except ImportError:
    traceback.print_exc()
    sys.exit(1)
except IOError:
    from django.core.exceptions import ImproperlyConfigured
    included_file = locals().get('__included_file__', '')
    if (not included_file or included_file == settings_file) and not os.path.exists(settings_file):
        if 'AWX_SETTINGS_FILE' not in os.environ:
            msg = 'No AWX configuration found at %s.' % settings_file
            msg += '\nDefine the AWX_SETTINGS_FILE environment variable to '
            msg += 'specify an alternate path.'
            raise ImproperlyConfigured(msg)
    raise
