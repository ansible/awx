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
    url(r'^(?P<pk>[0-9]+)/$', InstanceGroupDetail.as_view(), name='instance_group_detail'),
    url(r'^(?P<pk>[0-9]+)/jobs/$', InstanceGroupUnifiedJobsList.as_view(), name='instance_group_unified_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/instances/$', InstanceGroupInstanceList.as_view(), name='instance_group_instance_list'),
]

__all__ = ['urls']
