# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import AdHocCommandEventDetail


urls = [
    re_path(r'^(?P<pk>[0-9]+)/$', AdHocCommandEventDetail.as_view(), name='ad_hoc_command_event_detail'),
]

__all__ = ['urls']
