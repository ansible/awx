# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

# Development settings for AWX project.

# Python
import sys
import traceback

# Django Split Settings
from split_settings.tools import optional, include

# Load default settings.
from defaults import *  # NOQA


MONGO_HOST = '127.0.0.1'
MONGO_PORT = 27017
MONGO_USERNAME = None
MONGO_PASSWORD = None
MONGO_DB = 'system_tracking_dev'

# Disable capturing all SQL queries when running celeryd in development.
if 'celeryd' in sys.argv:
    SQL_DEBUG = False

# Use a different callback consumer/queue for development, to avoid a conflict
# if there is also a nightly install running on the development machine.
CALLBACK_CONSUMER_PORT = "tcp://127.0.0.1:5557"
CALLBACK_QUEUE_PORT = "ipc:///tmp/callback_receiver_dev.ipc"

# Enable PROOT for tower-qa integration tests
AWX_PROOT_ENABLED = True

# Use Django-Jenkins if installed. Only run tests for awx.main app.
try:
    import django_jenkins
    INSTALLED_APPS += (django_jenkins.__name__,)
    PROJECT_APPS = ('awx.main.tests', 'awx.api.tests', 'awx.fact.tests',)
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

# If there is an `/etc/tower/settings.py`, include it.
# If there is a `/etc/tower/conf.d/*.py`, include them.
include(optional('/etc/tower/settings.py'), scope=locals())
include(optional('/etc/tower/conf.d/*.py'), scope=locals())


# If any local_*.py files are present in awx/settings/, use them to override
# default settings for development.  If not present, we can still run using
# only the defaults.
try:
    include(
        optional('local_*.py'),
        scope=locals(),
    )
except ImportError:
    traceback.print_exc()
    sys.exit(1)
