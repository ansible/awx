# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    ScheduleList,
    ScheduleDetail,
    ScheduleUnifiedJobsList,
)


urls = [
    url(r'^$', ScheduleList.as_view(), name='schedule_list'),
    url(r'^(?P<pk>[0-9]+)/$', ScheduleDetail.as_view(), name='schedule_detail'),
    url(r'^(?P<pk>[0-9]+)/jobs/$', ScheduleUnifiedJobsList.as_view(), name='schedule_unified_jobs_list'),
]

__all__ = ['urls']
