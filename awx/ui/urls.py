# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf import settings
from django.conf.urls import *

urlpatterns = patterns('awx.ui.views',
    url(r'^$', 'index', name='index'),
    url(r'^migrations_notran/$', 'migrations_notran', name='migrations_notran'),
    url(r'^portal/$', 'portal_redirect', name='portal_redirect'),
)
