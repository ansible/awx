# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url
from awx.ui.views import (
    index,
    portal_redirect,
    migrations_notran,
)


app_name = 'ui'
urlpatterns = [ 
    url(r'^$', index, name='index'),
    url(r'^migrations_notran/$', migrations_notran, name='migrations_notran'),
    url(r'^portal/$', portal_redirect, name='portal_redirect'),
]
