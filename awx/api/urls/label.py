# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views.labels import LabelList, LabelDetail


urls = [re_path(r'^$', LabelList.as_view(), name='label_list'), re_path(r'^(?P<pk>[0-9]+)/$', LabelDetail.as_view(), name='label_detail')]

__all__ = ['urls']
