# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    AdHocCommandList,
    AdHocCommandDetail,
    AdHocCommandCancel,
    AdHocCommandRelaunch,
    AdHocCommandAdHocCommandEventsList,
    AdHocCommandActivityStreamList,
    AdHocCommandNotificationsList,
    AdHocCommandStdout,
)


urls = [
    re_path(r'^$', AdHocCommandList.as_view(), name='ad_hoc_command_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', AdHocCommandDetail.as_view(), name='ad_hoc_command_detail'),
    re_path(r'^(?P<pk>[0-9]+)/cancel/$', AdHocCommandCancel.as_view(), name='ad_hoc_command_cancel'),
    re_path(r'^(?P<pk>[0-9]+)/relaunch/$', AdHocCommandRelaunch.as_view(), name='ad_hoc_command_relaunch'),
    re_path(r'^(?P<pk>[0-9]+)/events/$', AdHocCommandAdHocCommandEventsList.as_view(), name='ad_hoc_command_ad_hoc_command_events_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', AdHocCommandActivityStreamList.as_view(), name='ad_hoc_command_activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/notifications/$', AdHocCommandNotificationsList.as_view(), name='ad_hoc_command_notifications_list'),
    re_path(r'^(?P<pk>[0-9]+)/stdout/$', AdHocCommandStdout.as_view(), name='ad_hoc_command_stdout'),
]

__all__ = ['urls']
