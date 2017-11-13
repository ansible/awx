# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    NotificationList,
    NotificationDetail,
)


urls = [
    url(r'^$', NotificationList.as_view(), name='notification_list'),
    url(r'^(?P<pk>[0-9]+)/$', NotificationDetail.as_view(), name='notification_detail'),
]

__all__ = ['urls']
