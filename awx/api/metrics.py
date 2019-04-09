# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    MetricsView
)


urls = [
    url(r'^$', MetricsView.as_view(), name='metrics_view'),
]

__all__ = ['urls']
