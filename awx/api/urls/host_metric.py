# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import HostMetricList, HostMetricDetail

urls = [re_path(r'$^', HostMetricList.as_view(), name='host_metric_list'), re_path(r'^(?P<pk>[0-9]+)/$', HostMetricDetail.as_view(), name='host_metric_detail')]

__all__ = ['urls']
