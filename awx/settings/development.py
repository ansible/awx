# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Development settings for AWX project.

# Python
import os
import socket
import copy
import sys
import traceback
import uuid

# Centos-7 doesn't include the svg mime type
# /usr/lib64/python/mimetypes.py
import mimetypes

# Django Split Settings
from split_settings.tools import optional, include

# Load default settings.
from .defaults import *  # NOQA

# awx-manage shell_plus --notebook
NOTEBOOK_ARGUMENTS = ['--NotebookApp.token=', '--ip', '0.0.0.0', '--port', '8888', '--allow-root', '--no-browser']

# print SQL queries in shell_plus
SHELL_PLUS_PRINT_SQL = False

# show colored logs in the dev environment
# to disable this, set `COLOR_LOGS = False` in awx/settings/local_settings.py
LOGGING['handlers']['console']['()'] = 'awx.main.utils.handlers.ColorHandler'  # noqa
# task system does not propagate to AWX, so color log these too
LOGGING['handlers']['task_system'] = LOGGING['handlers']['console'].copy()  # noqa
COLOR_LOGS = True

ALLOWED_HOSTS = ['*']

mimetypes.add_type("image/svg+xml", ".svg", True)
mimetypes.add_type("image/svg+xml", ".svgz", True)

# Disallow sending session cookies over insecure connections
SESSION_COOKIE_SECURE = False

# Disallow sending csrf cookies over insecure connections
CSRF_COOKIE_SECURE = False

# Disable Pendo on the UI for development/test.
# Note: This setting may be overridden by database settings.
PENDO_TRACKING_STATE = "off"
INSIGHTS_TRACKING_STATE = False

# debug toolbar and swagger assume that requirements/requirements_dev.txt are installed

INSTALLED_APPS += ['rest_framework_swagger', 'debug_toolbar']  # NOQA

MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE  # NOQA

DEBUG_TOOLBAR_CONFIG = {'ENABLE_STACKTRACES': True}

# Configure a default UUID for development only.
SYSTEM_UUID = '00000000-0000-0000-0000-000000000000'
INSTALL_UUID = '00000000-0000-0000-0000-000000000000'

# Store a snapshot of default settings at this point before loading any
# customizable config files.
DEFAULTS_SNAPSHOT = {}
this_module = sys.modules[__name__]
for setting in dir(this_module):
    if setting == setting.upper():
        DEFAULTS_SNAPSHOT[setting] = copy.deepcopy(getattr(this_module, setting))

# If there is an `/etc/tower/settings.py`, include it.
# If there is a `/etc/tower/conf.d/*.py`, include them.
include(optional('/etc/tower/settings.py'), scope=locals())
include(optional('/etc/tower/conf.d/*.py'), scope=locals())

BASE_VENV_PATH = "/var/lib/awx/venv/"
AWX_VENV_PATH = os.path.join(BASE_VENV_PATH, "awx")

# Use SQLite for unit tests instead of PostgreSQL.  If the lines below are
# commented out, Django will create the test_awx-dev database in PostgreSQL to
# run unit tests.
if "pytest" in sys.modules:
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-{}'.format(str(uuid.uuid4()))}}
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'awx.sqlite3'),  # noqa
            'TEST': {
                # Test database cannot be :memory: for inventory tests.
                'NAME': os.path.join(BASE_DIR, 'awx_test.sqlite3')  # noqa
            },
        }
    }

CLUSTER_HOST_ID = socket.gethostname()

AWX_CALLBACK_PROFILE = True

# ======================!!!!!!! FOR DEVELOPMENT ONLY !!!!!!!=================================
# Disable normal scheduled/triggered task managers (DependencyManager, TaskManager, WorkflowManager).
# Allows user to trigger task managers directly for debugging and profiling purposes.
# Only works in combination with settings.SETTINGS_MODULE == 'awx.settings.development'
AWX_DISABLE_TASK_MANAGERS = False
# ======================!!!!!!! FOR DEVELOPMENT ONLY !!!!!!!=================================

if 'sqlite3' not in DATABASES['default']['ENGINE']:  # noqa
    DATABASES['default'].setdefault('OPTIONS', dict()).setdefault('application_name', f'{CLUSTER_HOST_ID}-{os.getpid()}-{" ".join(sys.argv)}'[:63])  # noqa

# Everywhere else we use /var/lib/awx/public/static/ - but this requires running collectstatic.
# This makes the browsable API work in the dev env without any additional steps.
STATIC_ROOT = os.path.join(BASE_DIR, 'public', 'static')

# If any local_*.py files are present in awx/settings/, use them to override
# default settings for development.  If not present, we can still run using
# only the defaults.
# this needs to stay at the bottom of this file
try:
    if os.getenv('AWX_KUBE_DEVEL', False):
        include(optional('minikube.py'), scope=locals())
    else:
        include(optional('local_*.py'), scope=locals())
except ImportError:
    traceback.print_exc()
    sys.exit(1)
