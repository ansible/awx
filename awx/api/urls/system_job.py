# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    SystemJobList,
    SystemJobDetail,
    SystemJobCancel,
    SystemJobNotificationsList,
    SystemJobEventsList
)


urls = [
    url(r'^$', SystemJobList.as_view(), name='system_job_list'),
    url(r'^(?P<pk>[0-9]+)/$', SystemJobDetail.as_view(), name='system_job_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$', SystemJobCancel.as_view(), name='system_job_cancel'),
    url(r'^(?P<pk>[0-9]+)/notifications/$', SystemJobNotificationsList.as_view(), name='system_job_notifications_list'),
    url(r'^(?P<pk>[0-9]+)/events/$', SystemJobEventsList.as_view(), name='system_job_events_list'),
]

__all__ = ['urls']
