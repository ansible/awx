# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

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
    url(r'^$', JobList.as_view(), name='job_list'),
    url(r'^(?P<pk>[0-9]+)/$', JobDetail.as_view(), name='job_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$', JobCancel.as_view(), name='job_cancel'),
    url(r'^(?P<pk>[0-9]+)/relaunch/$', JobRelaunch.as_view(), name='job_relaunch'),
    url(r'^(?P<pk>[0-9]+)/create_schedule/$', JobCreateSchedule.as_view(), name='job_create_schedule'),
    url(r'^(?P<pk>[0-9]+)/job_host_summaries/$', JobJobHostSummariesList.as_view(), name='job_job_host_summaries_list'),
    url(r'^(?P<pk>[0-9]+)/job_events/$', JobJobEventsList.as_view(), name='job_job_events_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$', JobActivityStreamList.as_view(), name='job_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/stdout/$', JobStdout.as_view(), name='job_stdout'),
    url(r'^(?P<pk>[0-9]+)/notifications/$', JobNotificationsList.as_view(), name='job_notifications_list'),
    url(r'^(?P<pk>[0-9]+)/labels/$', JobLabelList.as_view(), name='job_label_list'),
    url(r'^(?P<pk>[0-9]+)/$', JobHostSummaryDetail.as_view(), name='job_host_summary_detail'),
]

__all__ = ['urls']
