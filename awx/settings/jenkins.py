# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Test settings for AWX project.

# Python
import glob

# Django Split Settings
from split_settings.tools import optional, include

# Load development settings.
from defaults  import *

# Load development settings.
from development import *

# Disable capturing DEBUG
DEBUG = False
TEMPLATE_DEBUG = DEBUG
SQL_DEBUG = DEBUG

# Use Django-Jenkins if installed. Only run tests for awx.main app.
import django_jenkins
INSTALLED_APPS += ('django_jenkins',)
PROJECT_APPS = ('awx.main', 'awx.api',)

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pylint',
    'django_jenkins.tasks.with_coverage',
    # 'django_jenkins.tasks.django_tests',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes',
    'django_jenkins.tasks.run_jshint',
    'django_jenkins.tasks.run_csslint',
    )
PEP8_RCFILE = "setup.cfg"
CSSLINT_CHECKED_FILES = glob.glob(os.path.join(BASE_DIR, 'ui/static/less/*.less'))
JSHINT_CHECKED_FILES = [os.path.join(BASE_DIR, 'ui/static/js'),
                        os.path.join(BASE_DIR, 'ui/static/lib/ansible'),]
