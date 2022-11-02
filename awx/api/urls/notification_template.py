# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    NotificationTemplateList,
    NotificationTemplateDetail,
    NotificationTemplateTest,
    NotificationTemplateNotificationList,
    NotificationTemplateCopy,
)


urls = [
    re_path(r'^$', NotificationTemplateList.as_view(), name='notification_template_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', NotificationTemplateDetail.as_view(), name='notification_template_detail'),
    re_path(r'^(?P<pk>[0-9]+)/test/$', NotificationTemplateTest.as_view(), name='notification_template_test'),
    re_path(r'^(?P<pk>[0-9]+)/notifications/$', NotificationTemplateNotificationList.as_view(), name='notification_template_notification_list'),
    re_path(r'^(?P<pk>[0-9]+)/copy/$', NotificationTemplateCopy.as_view(), name='notification_template_copy'),
]

__all__ = ['urls']
