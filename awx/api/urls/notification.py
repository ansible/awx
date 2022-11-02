# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import NotificationList, NotificationDetail


urls = [
    re_path(r'^$', NotificationList.as_view(), name='notification_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', NotificationDetail.as_view(), name='notification_detail'),
]

__all__ = ['urls']
