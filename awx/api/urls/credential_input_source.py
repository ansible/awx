# Copyright (c) 2019 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    CredentialInputSourceDetail,
    CredentialInputSourceList,
)


urls = [
    url(r'^$', CredentialInputSourceList.as_view(), name='credential_input_source_list'),
    url(r'^(?P<pk>[0-9]+)/$', CredentialInputSourceDetail.as_view(), name='credential_input_source_detail'),
]

__all__ = ['urls']
