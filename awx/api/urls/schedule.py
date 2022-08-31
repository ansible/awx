# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import ScheduleList, ScheduleDetail, ScheduleUnifiedJobsList, ScheduleCredentialsList, ScheduleLabelsList, ScheduleInstanceGroupList


urls = [
    re_path(r'^$', ScheduleList.as_view(), name='schedule_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', ScheduleDetail.as_view(), name='schedule_detail'),
    re_path(r'^(?P<pk>[0-9]+)/jobs/$', ScheduleUnifiedJobsList.as_view(), name='schedule_unified_jobs_list'),
    re_path(r'^(?P<pk>[0-9]+)/credentials/$', ScheduleCredentialsList.as_view(), name='schedule_credentials_list'),
    re_path(r'^(?P<pk>[0-9]+)/labels/$', ScheduleLabelsList.as_view(), name='schedule_labels_list'),
    re_path(r'^(?P<pk>[0-9]+)/instance_groups/$', ScheduleInstanceGroupList.as_view(), name='schedule_instance_groups_list'),
]

__all__ = ['urls']
