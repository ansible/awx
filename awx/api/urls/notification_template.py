# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    NotificationTemplateList,
    NotificationTemplateDetail,
    NotificationTemplateTest,
    NotificationTemplateNotificationList,
    NotificationTemplateCopy,
)


urls = [
    url(r'^$', NotificationTemplateList.as_view(), name='notification_template_list'),
    url(r'^(?P<pk>[0-9]+)/$', NotificationTemplateDetail.as_view(), name='notification_template_detail'),
    url(r'^(?P<pk>[0-9]+)/test/$', NotificationTemplateTest.as_view(), name='notification_template_test'),
    url(r'^(?P<pk>[0-9]+)/notifications/$', NotificationTemplateNotificationList.as_view(), name='notification_template_notification_list'),
    url(r'^(?P<pk>[0-9]+)/copy/$', NotificationTemplateCopy.as_view(), name='notification_template_copy'),
]

__all__ = ['urls']
