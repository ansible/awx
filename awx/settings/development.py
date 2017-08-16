# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Development settings for AWX project.

# Python
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
from defaults import *  # NOQA

# show colored logs in the dev environment
# to disable this, set `COLOR_LOGS = False` in awx/settings/local_settings.py
LOGGING['handlers']['console']['()'] = 'awx.main.utils.handlers.ColorHandler'
COLOR_LOGS = True

# Pipe management playbook output to console
LOGGING['loggers']['awx.isolated.manager.playbooks']['propagate'] = True

ALLOWED_HOSTS = ['*']

mimetypes.add_type("image/svg+xml", ".svg", True)
mimetypes.add_type("image/svg+xml", ".svgz", True)

# Disallow sending session cookies over insecure connections
SESSION_COOKIE_SECURE = False

# Disallow sending csrf cookies over insecure connections
CSRF_COOKIE_SECURE = False

# Override django.template.loaders.cached.Loader in defaults.py
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# Disable capturing all SQL queries when running celeryd in development.
if 'celeryd' in sys.argv:
    SQL_DEBUG = False

CELERYD_HIJACK_ROOT_LOGGER = False
CELERYD_LOG_COLOR = True

CALLBACK_QUEUE = "callback_tasks"

# Enable PROOT for tower-qa integration tests.
# Note: This setting may be overridden by database settings.
AWX_PROOT_ENABLED = True

AWX_ISOLATED_USERNAME = 'root'
AWX_ISOLATED_CHECK_INTERVAL = 1
AWX_ISOLATED_LAUNCH_TIMEOUT = 30

# Disable Pendo on the UI for development/test.
# Note: This setting may be overridden by database settings.
PENDO_TRACKING_STATE = "off"

# Use Django-Jenkins if installed. Only run tests for awx.main app.
try:
    import django_jenkins
    INSTALLED_APPS += (django_jenkins.__name__,)
    PROJECT_APPS = ('awx.main.tests', 'awx.api.tests',)
except ImportError:
    pass

if 'django_jenkins' in INSTALLED_APPS:
    JENKINS_TASKS = (
        # 'django_jenkins.tasks.run_pylint',
        # 'django_jenkins.tasks.run_flake8',
        # The following are not needed when including run_flake8
        # 'django_jenkins.tasks.run_pep8',
        # 'django_jenkins.tasks.run_pyflakes',
        # The following are handled by various grunt tasks and no longer required
        # 'django_jenkins.tasks.run_jshint',
        # 'django_jenkins.tasks.run_csslint',
    )
    PEP8_RCFILE = "setup.cfg"
    PYLINT_RCFILE = ".pylintrc"

# Much faster than the default
# https://docs.djangoproject.com/en/1.6/topics/auth/passwords/#how-django-stores-passwords
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
)

# Configure a default UUID for development only.
SYSTEM_UUID = '00000000-0000-0000-0000-000000000000'

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

ANSIBLE_VENV_PATH = "/venv/ansible"
AWX_VENV_PATH = "/venv/awx"

# If any local_*.py files are present in awx/settings/, use them to override
# default settings for development.  If not present, we can still run using
# only the defaults.
try:
    include(optional('local_*.py'), scope=locals())
except ImportError:
    traceback.print_exc()
    sys.exit(1)

CLUSTER_HOST_ID = socket.gethostname()
CELERY_ROUTES['awx.main.tasks.cluster_node_heartbeat'] = {'queue': CLUSTER_HOST_ID, 'routing_key': CLUSTER_HOST_ID}
# Production only runs this schedule on controlling nodes
# but development will just run it on all nodes
CELERY_ROUTES['awx.main.tasks.awx_isolated_heartbeat'] = {'queue': CLUSTER_HOST_ID, 'routing_key': CLUSTER_HOST_ID}
CELERYBEAT_SCHEDULE['isolated_heartbeat'] = {
    'task': 'awx.main.tasks.awx_isolated_heartbeat',
    'schedule': timedelta(seconds = AWX_ISOLATED_PERIODIC_CHECK),
    'options': {'expires': AWX_ISOLATED_PERIODIC_CHECK * 2,}
}

# Supervisor service name dictionary used for programatic restart
SERVICE_NAME_DICT = {
    "celery": "celeryd",
    "callback": "receiver",
    "runworker": "channels",
    "uwsgi": "uwsgi",
    "daphne": "daphne",
    "nginx": "nginx"}
# Used for sending commands in automatic restart
UWSGI_FIFO_LOCATION = '/awxfifo'

