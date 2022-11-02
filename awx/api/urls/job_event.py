# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import JobEventDetail, JobEventChildrenList

urls = [
    re_path(r'^(?P<pk>[0-9]+)/$', JobEventDetail.as_view(), name='job_event_detail'),
    re_path(r'^(?P<pk>[0-9]+)/children/$', JobEventChildrenList.as_view(), name='job_event_children_list'),
]

__all__ = ['urls']
