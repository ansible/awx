# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    ActivityStreamList,
    ActivityStreamDetail,
)


urls = [
    url(r'^$', ActivityStreamList.as_view(), name='activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/$', ActivityStreamDetail.as_view(), name='activity_stream_detail'),
]

__all__ = ['urls']
