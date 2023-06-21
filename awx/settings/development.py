# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Development settings for AWX project.

# Python
import os
import socket
import copy
import sys
import traceback

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

INSTALLED_APPS += ['drf_yasg', 'debug_toolbar']  # NOQA

MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE  # NOQA

DEBUG_TOOLBAR_CONFIG = {'ENABLE_STACKTRACES': True}

# Configure a default UUID for development only.
SYSTEM_UUID = '00000000-0000-0000-0000-000000000000'
INSTALL_UUID = '00000000-0000-0000-0000-000000000000'

# Ansible base virtualenv paths and enablement
# only used for deprecated fields and management commands for them
BASE_VENV_PATH = os.path.realpath("/var/lib/awx/venv")

CLUSTER_HOST_ID = socket.gethostname()

AWX_CALLBACK_PROFILE = True

# ======================!!!!!!! FOR DEVELOPMENT ONLY !!!!!!!=================================
# Disable normal scheduled/triggered task managers (DependencyManager, TaskManager, WorkflowManager).
# Allows user to trigger task managers directly for debugging and profiling purposes.
# Only works in combination with settings.SETTINGS_MODULE == 'awx.settings.development'
AWX_DISABLE_TASK_MANAGERS = False
# ======================!!!!!!! FOR DEVELOPMENT ONLY !!!!!!!=================================

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

# If there is an `/etc/tower/settings.py`, include it.
# If there is a `/etc/tower/conf.d/*.py`, include them.
include(optional('/etc/tower/settings.py'), scope=locals())
include(optional('/etc/tower/conf.d/*.py'), scope=locals())

# If any local_*.py files are present in awx/settings/, use them to override
# default settings for development.  If not present, we can still run using
# only the defaults.
# this needs to stay at the bottom of this file
try:
    if os.getenv('AWX_KUBE_DEVEL', False):
        include(optional('development_kube.py'), scope=locals())
    else:
        include(optional('local_*.py'), scope=locals())
except ImportError:
    traceback.print_exc()
    sys.exit(1)

# The below runs AFTER all of the custom settings are imported
# because conf.d files will define DATABASES and this should modify that
from .application_name import set_application_name

set_application_name(DATABASES, CLUSTER_HOST_ID)  # NOQA

del set_application_name
