# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import CredentialTypeList, CredentialTypeDetail, CredentialTypeCredentialList, CredentialTypeActivityStreamList, CredentialTypeExternalTest


urls = [
    re_path(r'^$', CredentialTypeList.as_view(), name='credential_type_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', CredentialTypeDetail.as_view(), name='credential_type_detail'),
    re_path(r'^(?P<pk>[0-9]+)/credentials/$', CredentialTypeCredentialList.as_view(), name='credential_type_credential_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', CredentialTypeActivityStreamList.as_view(), name='credential_type_activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/test/$', CredentialTypeExternalTest.as_view(), name='credential_type_external_test'),
]

__all__ = ['urls']
