# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import SystemJobList, SystemJobDetail, SystemJobCancel, SystemJobNotificationsList, SystemJobEventsList


urls = [
    re_path(r'^$', SystemJobList.as_view(), name='system_job_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', SystemJobDetail.as_view(), name='system_job_detail'),
    re_path(r'^(?P<pk>[0-9]+)/cancel/$', SystemJobCancel.as_view(), name='system_job_cancel'),
    re_path(r'^(?P<pk>[0-9]+)/notifications/$', SystemJobNotificationsList.as_view(), name='system_job_notifications_list'),
    re_path(r'^(?P<pk>[0-9]+)/events/$', SystemJobEventsList.as_view(), name='system_job_events_list'),
]

__all__ = ['urls']
