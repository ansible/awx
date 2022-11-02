# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import ActivityStreamList, ActivityStreamDetail


urls = [
    re_path(r'^$', ActivityStreamList.as_view(), name='activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', ActivityStreamDetail.as_view(), name='activity_stream_detail'),
]

__all__ = ['urls']
