# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import InstanceList, InstanceDetail, InstanceUnifiedJobsList, InstanceInstanceGroupsList, InstanceHealthCheck, InstanceInstallBundle


urls = [
    re_path(r'^$', InstanceList.as_view(), name='instance_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', InstanceDetail.as_view(), name='instance_detail'),
    re_path(r'^(?P<pk>[0-9]+)/jobs/$', InstanceUnifiedJobsList.as_view(), name='instance_unified_jobs_list'),
    re_path(r'^(?P<pk>[0-9]+)/instance_groups/$', InstanceInstanceGroupsList.as_view(), name='instance_instance_groups_list'),
    re_path(r'^(?P<pk>[0-9]+)/health_check/$', InstanceHealthCheck.as_view(), name='instance_health_check'),
    re_path(r'^(?P<pk>[0-9]+)/install_bundle/$', InstanceInstallBundle.as_view(), name='instance_install_bundle'),
]

__all__ = ['urls']
