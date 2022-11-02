# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import MetricsView


urls = [re_path(r'^$', MetricsView.as_view(), name='metrics_view')]

__all__ = ['urls']
