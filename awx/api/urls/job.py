# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    JobList,
    JobDetail,
    JobCancel,
    JobRelaunch,
    JobCreateSchedule,
    JobJobHostSummariesList,
    JobJobEventsList,
    JobActivityStreamList,
    JobStdout,
    JobNotificationsList,
    JobLabelList,
    JobHostSummaryDetail,
)


urls = [
    re_path(r'^$', JobList.as_view(), name='job_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', JobDetail.as_view(), name='job_detail'),
    re_path(r'^(?P<pk>[0-9]+)/cancel/$', JobCancel.as_view(), name='job_cancel'),
    re_path(r'^(?P<pk>[0-9]+)/relaunch/$', JobRelaunch.as_view(), name='job_relaunch'),
    re_path(r'^(?P<pk>[0-9]+)/create_schedule/$', JobCreateSchedule.as_view(), name='job_create_schedule'),
    re_path(r'^(?P<pk>[0-9]+)/job_host_summaries/$', JobJobHostSummariesList.as_view(), name='job_job_host_summaries_list'),
    re_path(r'^(?P<pk>[0-9]+)/job_events/$', JobJobEventsList.as_view(), name='job_job_events_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', JobActivityStreamList.as_view(), name='job_activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/stdout/$', JobStdout.as_view(), name='job_stdout'),
    re_path(r'^(?P<pk>[0-9]+)/notifications/$', JobNotificationsList.as_view(), name='job_notifications_list'),
    re_path(r'^(?P<pk>[0-9]+)/labels/$', JobLabelList.as_view(), name='job_label_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', JobHostSummaryDetail.as_view(), name='job_host_summary_detail'),
]

__all__ = ['urls']
