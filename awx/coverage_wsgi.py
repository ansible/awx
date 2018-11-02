# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import coverage
import atexit

import django  # NOQA

from .wsgi import get_wsgi_application


"""
WSGI config for AWX project with code coverage metric collection enabled.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""
global cov
cov = coverage.Coverage()
cov.start()
print('!*!*!*!*!*!*!* STARTING COVERAGE DATA COLLECTION !*!*!*!*!*!*!*')

@atexit.register
def stop_coverage():
    cov.stop()
    cov.save()
    print('!*!*!*!*!*!*!* SAVED COVERAGE DATA !*!*!*!*!*!*!*')


application = get_wsgi_application()
