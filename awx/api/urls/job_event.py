# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    JobEventList,
    JobEventDetail,
    JobEventChildrenList,
    JobEventHostsList,
)


urls = [
    url(r'^$', JobEventList.as_view(), name='job_event_list'),
    url(r'^(?P<pk>[0-9]+)/$', JobEventDetail.as_view(), name='job_event_detail'),
    url(r'^(?P<pk>[0-9]+)/children/$', JobEventChildrenList.as_view(), name='job_event_children_list'),
    url(r'^(?P<pk>[0-9]+)/hosts/$', JobEventHostsList.as_view(), name='job_event_hosts_list'),
]

__all__ = ['urls']
