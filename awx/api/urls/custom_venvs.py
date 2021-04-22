# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import CustomVenvs


urls = [
    url(r'^$', CustomVenvs.as_view(), name='custom_venvs'),
    url(r'^(?P<pk>[0-9]+)/$', CustomVenvs.as_view(), name='custom_venvs_detail'),
]

__all__ = ['urls']
