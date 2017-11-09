# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    LabelList,
    LabelDetail,
)


urls = [
    url(r'^$', LabelList.as_view(), name='label_list'),
    url(r'^(?P<pk>[0-9]+)/$', LabelDetail.as_view(), name='label_detail'),
]

__all__ = ['urls']
