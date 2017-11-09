# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    InstanceList,
    InstanceDetail,
    InstanceUnifiedJobsList,
    InstanceInstanceGroupsList,
)


urls = [
    url(r'^$', InstanceList.as_view(), name='instance_list'),
    url(r'^(?P<pk>[0-9]+)/$', InstanceDetail.as_view()),
    url(r'^(?P<pk>[0-9]+)/jobs/$', InstanceUnifiedJobsList.as_view()),
    url(r'^(?P<pk>[0-9]+)/instance_groups/$', InstanceInstanceGroupsList.as_view()),
]

__all__ = ['urls']
