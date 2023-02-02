# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import HostMetricList

urls = [re_path(r'$^', HostMetricList.as_view(), name='host_metric_list')]

__all__ = ['urls']
