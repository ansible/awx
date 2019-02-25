# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    CredentialTypeList,
    CredentialTypeDetail,
    CredentialTypeCredentialList,
    CredentialTypeActivityStreamList,
    CredentialTypeExternalTest,
)


urls = [
    url(r'^$', CredentialTypeList.as_view(), name='credential_type_list'),
    url(r'^(?P<pk>[0-9]+)/$', CredentialTypeDetail.as_view(), name='credential_type_detail'),
    url(r'^(?P<pk>[0-9]+)/credentials/$', CredentialTypeCredentialList.as_view(), name='credential_type_credential_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$', CredentialTypeActivityStreamList.as_view(), name='credential_type_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/test/$', CredentialTypeExternalTest.as_view(), name='credential_type_external_test'),
]

__all__ = ['urls']
