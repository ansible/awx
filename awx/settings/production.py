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

# Absolute filesystem path to the directory for job status stdout
# This directory should not be web-accessible
JOBOUTPUT_ROOT = '/var/lib/awx/job_status/'

# The heartbeat file for the tower scheduler
SCHEDULE_METADATA_LOCATION = '/var/lib/awx/.tower_cycle'

# Ansible base virtualenv paths and enablement
BASE_VENV_PATH = os.path.realpath("/var/lib/awx/venv")
ANSIBLE_VENV_PATH = os.path.join(BASE_VENV_PATH, "ansible")

# Tower base virtualenv paths and enablement
AWX_VENV_PATH = os.path.join(BASE_VENV_PATH, "awx")

AWX_ISOLATED_USERNAME = 'awx'

LOGGING['handlers']['tower_warnings']['filename'] = '/var/log/tower/tower.log'  # noqa
LOGGING['handlers']['callback_receiver']['filename'] = '/var/log/tower/callback_receiver.log'  # noqa
LOGGING['handlers']['dispatcher']['filename'] = '/var/log/tower/dispatcher.log'  # noqa
LOGGING['handlers']['wsbroadcast']['filename'] = '/var/log/tower/wsbroadcast.log'  # noqa
LOGGING['handlers']['task_system']['filename'] = '/var/log/tower/task_system.log'  # noqa
LOGGING['handlers']['management_playbooks']['filename'] = '/var/log/tower/management_playbooks.log'  # noqa
LOGGING['handlers']['system_tracking_migrations']['filename'] = '/var/log/tower/tower_system_tracking_migrations.log'  # noqa
LOGGING['handlers']['rbac_migrations']['filename'] = '/var/log/tower/tower_rbac_migrations.log'  # noqa

# Store a snapshot of default settings at this point before loading any
# customizable config files.
DEFAULTS_SNAPSHOT = {}
this_module = sys.modules[__name__]
for setting in dir(this_module):
    if setting == setting.upper():
        DEFAULTS_SNAPSHOT[setting] = copy.deepcopy(getattr(this_module, setting))

# Load settings from any .py files in the global conf.d directory specified in
# the environment, defaulting to /etc/tower/conf.d/.
settings_dir = os.environ.get('AWX_SETTINGS_DIR', '/etc/tower/conf.d/')
settings_files = os.path.join(settings_dir, '*.py')

# Load remaining settings from the global settings file specified in the
# environment, defaulting to /etc/tower/settings.py.
settings_file = os.environ.get('AWX_SETTINGS_FILE',
                               '/etc/tower/settings.py')

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
    if (not included_file or included_file == settings_file):
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

# The below runs AFTER all of the custom settings are imported.

CELERYBEAT_SCHEDULE.update({  # noqa
    'isolated_heartbeat': {
        'task': 'awx.main.tasks.awx_isolated_heartbeat',
        'schedule': timedelta(seconds=AWX_ISOLATED_PERIODIC_CHECK),  # noqa
        'options': {'expires': AWX_ISOLATED_PERIODIC_CHECK * 2},  # noqa
    }
})

DATABASES['default'].setdefault('OPTIONS', dict()).setdefault('application_name', f'{CLUSTER_HOST_ID}-{os.getpid()}-{" ".join(sys.argv)}'[:63]) # noqa
