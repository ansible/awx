#!/usr/bin/env python
import os
import sys

from django.conf import settings

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'taggit',
            'taggit.tests',
        ]
    )


from django.test.simple import DjangoTestSuiteRunner

def runtests():
    runner = DjangoTestSuiteRunner()
    failures = runner.run_tests(['tests'], verbosity=1, interactive=True)
    sys.exit(failures)

if __name__ == '__main__':
    runtests(*sys.argv[1:])

