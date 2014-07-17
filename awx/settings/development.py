# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Development settings for AWX project.

# Python
import sys
import traceback
import glob

# Django Split Settings
from split_settings.tools import optional, include

# Load default settings.
from defaults import *

# Disable capturing all SQL queries when running celeryd in development.
if 'celeryd' in sys.argv:
    SQL_DEBUG = False

# Use a different callback consumer/queue for development, to avoid a conflict
# if there is also a nightly install running on the development machine.
CALLBACK_CONSUMER_PORT = "tcp://127.0.0.1:5557"
CALLBACK_QUEUE_PORT = "ipc:///tmp/callback_receiver_dev.ipc"

# Use Django-Jenkins if installed. Only run tests for awx.main app.
try:
    import django_jenkins
    INSTALLED_APPS += ('django_jenkins',)
    PROJECT_APPS = ('awx.main', 'awx.api',)
except ImportError:
    pass

if 'django_jenkins' in INSTALLED_APPS:
    JENKINS_TASKS = (
        'django_jenkins.tasks.run_pylint',
        'django_jenkins.tasks.with_coverage',
        'django_jenkins.tasks.django_tests',
        'django_jenkins.tasks.run_pep8',
        'django_jenkins.tasks.run_pyflakes',
        'django_jenkins.tasks.run_jshint',
        'django_jenkins.tasks.run_csslint',
        )
    PEP8_RCFILE = "setup.cfg"
    PYLINT_RCFILE = ".pylintrc"
    CSSLINT_CHECKED_FILES = glob.glob(os.path.join(BASE_DIR, 'ui/static/less/*.less'))
    JSHINT_CHECKED_FILES = [os.path.join(BASE_DIR, 'ui/static/js'),
                            os.path.join(BASE_DIR, 'ui/static/lib/ansible'),]

# If there is an `/etc/tower/settings.py`, include it.
include(optional('/etc/tower/settings.py'), scope=locals())

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
