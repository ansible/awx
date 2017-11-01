# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    ScheduleList,
    ScheduleDetail,
    ScheduleUnifiedJobsList,
    ScheduleCredentialsList,
)


urls = [
    url(r'^$', ScheduleList.as_view(), name='schedule_list'),
    url(r'^(?P<pk>[0-9]+)/$', ScheduleDetail.as_view(), name='schedule_detail'),
    url(r'^(?P<pk>[0-9]+)/jobs/$', ScheduleUnifiedJobsList.as_view(), name='schedule_unified_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$', ScheduleCredentialsList.as_view(), name='schedule_credentials_list'),
]

__all__ = ['urls']
