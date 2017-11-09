# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    AdHocCommandEventList,
    AdHocCommandEventDetail,
)


urls = [
    url(r'^$', AdHocCommandEventList.as_view(), name='ad_hoc_command_event_list'),
    url(r'^(?P<pk>[0-9]+)/$', AdHocCommandEventDetail.as_view(), name='ad_hoc_command_event_detail'),
]

__all__ = ['urls']
