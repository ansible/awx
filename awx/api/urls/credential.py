# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    CredentialList,
    CredentialActivityStreamList,
    CredentialDetail,
    CredentialAccessList,
    CredentialObjectRolesList,
    CredentialOwnerUsersList,
    CredentialOwnerTeamsList,
    CredentialCopy,
    CredentialInputSourceSubList,
    CredentialExternalTest,
)


urls = [
    re_path(r'^$', CredentialList.as_view(), name='credential_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', CredentialActivityStreamList.as_view(), name='credential_activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', CredentialDetail.as_view(), name='credential_detail'),
    re_path(r'^(?P<pk>[0-9]+)/access_list/$', CredentialAccessList.as_view(), name='credential_access_list'),
    re_path(r'^(?P<pk>[0-9]+)/object_roles/$', CredentialObjectRolesList.as_view(), name='credential_object_roles_list'),
    re_path(r'^(?P<pk>[0-9]+)/owner_users/$', CredentialOwnerUsersList.as_view(), name='credential_owner_users_list'),
    re_path(r'^(?P<pk>[0-9]+)/owner_teams/$', CredentialOwnerTeamsList.as_view(), name='credential_owner_teams_list'),
    re_path(r'^(?P<pk>[0-9]+)/copy/$', CredentialCopy.as_view(), name='credential_copy'),
    re_path(r'^(?P<pk>[0-9]+)/input_sources/$', CredentialInputSourceSubList.as_view(), name='credential_input_source_sublist'),
    re_path(r'^(?P<pk>[0-9]+)/test/$', CredentialExternalTest.as_view(), name='credential_external_test'),
]

__all__ = ['urls']
