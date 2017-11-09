# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    JobHostSummaryDetail,
)


urls = [
    url(r'^(?P<pk>[0-9]+)/$', JobHostSummaryDetail.as_view(), name='job_host_summary_detail'),
]

__all__ = ['urls']
