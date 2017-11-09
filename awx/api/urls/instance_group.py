# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    InstanceGroupList,
    InstanceGroupDetail,
    InstanceGroupUnifiedJobsList,
    InstanceGroupInstanceList,
)


urls = [
    url(r'^$', InstanceGroupList.as_view(), name='instance_group_list'),
    url(r'^(?P<pk>[0-9]+)/$', InstanceGroupDetail.as_view()),
    url(r'^(?P<pk>[0-9]+)/jobs/$', InstanceGroupUnifiedJobsList.as_view()),
    url(r'^(?P<pk>[0-9]+)/instances/$', InstanceGroupInstanceList.as_view()),
]

__all__ = ['urls']
