# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import JobEventDetail, JobEventChildrenList

urls = [
    url(r'^(?P<pk>[0-9]+)/$', JobEventDetail.as_view(), name='job_event_detail'),
    url(r'^(?P<pk>[0-9]+)/children/$', JobEventChildrenList.as_view(), name='job_event_children_list'),
]

__all__ = ['urls']
