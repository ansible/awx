# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Production settings for AWX project.

# Python
import os
import copy
import errno
import sys
import traceback

# Django Split Settings
from split_settings.tools import optional, include

# Load default settings.
from .defaults import *  # NOQA

DEBUG = False
TEMPLATE_DEBUG = DEBUG
SQL_DEBUG = DEBUG

# Clear database settings to force production environment to define them.
DATABASES = {}

# Clear the secret key to force production environment to define it.
SECRET_KEY = None

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Ansible base virtualenv paths and enablement
# only used for deprecated fields and management commands for them
BASE_VENV_PATH = os.path.realpath("/var/lib/awx/venv")

# Very important that this is editable (not read_only) in the API
AWX_ISOLATION_SHOW_PATHS = [
    '/etc/pki/ca-trust:/etc/pki/ca-trust:O',
    '/usr/share/pki:/usr/share/pki:O',
]

# Store a snapshot of default settings at this point before loading any
# customizable config files.
this_module = sys.modules[__name__]
local_vars = dir(this_module)
DEFAULTS_SNAPSHOT = {}  # define after we save local_vars so we do not snapshot the snapshot
for setting in local_vars:
    if setting.isupper():
        DEFAULTS_SNAPSHOT[setting] = copy.deepcopy(getattr(this_module, setting))

del local_vars  # avoid temporary variables from showing up in dir(settings)
del this_module
#
###############################################################################################
#
#  Any settings defined after this point will be marked as as a read_only database setting
#
################################################################################################

# Load settings from any .py files in the global conf.d directory specified in
# the environment, defaulting to /etc/tower/conf.d/.
settings_dir = os.environ.get('AWX_SETTINGS_DIR', '/etc/tower/conf.d/')
settings_files = os.path.join(settings_dir, '*.py')

# Load remaining settings from the global settings file specified in the
# environment, defaulting to /etc/tower/settings.py.
settings_file = os.environ.get('AWX_SETTINGS_FILE', '/etc/tower/settings.py')

# Attempt to load settings from /etc/tower/settings.py first, followed by
# /etc/tower/conf.d/*.py.
try:
    include(settings_file, optional(settings_files), scope=locals())
except ImportError:
    traceback.print_exc()
    sys.exit(1)
except IOError:
    from django.core.exceptions import ImproperlyConfigured

    included_file = locals().get('__included_file__', '')
    if not included_file or included_file == settings_file:
        # The import doesn't always give permission denied, so try to open the
        # settings file directly.
        try:
            e = None
            open(settings_file)
        except IOError:
            pass
        if e and e.errno == errno.EACCES:
            SECRET_KEY = 'permission-denied'
            LOGGING = {}
        else:
            msg = 'No AWX configuration found at %s.' % settings_file
            msg += '\nDefine the AWX_SETTINGS_FILE environment variable to '
            msg += 'specify an alternate path.'
            raise ImproperlyConfigured(msg)
    else:
        raise

# The below runs AFTER all of the custom settings are imported
# because conf.d files will define DATABASES and this should modify that
from .application_name import set_application_name

set_application_name(DATABASES, CLUSTER_HOST_ID)  # NOQA

del set_application_name
