
# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from __future__ import absolute_import, unicode_literals

import os
from celery import Celery
from django.conf import settings # noqa


try:
    import awx.devonly # noqa
    MODE = 'development'
except ImportError: # pragma: no cover
    MODE = 'production'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'awx.settings.%s' % MODE)

app = Celery('awx')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

if __name__ == '__main__':
    app.start()
