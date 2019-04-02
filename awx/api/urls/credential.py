# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

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
    url(r'^$', CredentialList.as_view(), name='credential_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$', CredentialActivityStreamList.as_view(), name='credential_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/$', CredentialDetail.as_view(), name='credential_detail'),
    url(r'^(?P<pk>[0-9]+)/access_list/$', CredentialAccessList.as_view(), name='credential_access_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$', CredentialObjectRolesList.as_view(), name='credential_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/owner_users/$', CredentialOwnerUsersList.as_view(), name='credential_owner_users_list'),
    url(r'^(?P<pk>[0-9]+)/owner_teams/$', CredentialOwnerTeamsList.as_view(), name='credential_owner_teams_list'),
    url(r'^(?P<pk>[0-9]+)/copy/$', CredentialCopy.as_view(), name='credential_copy'),
    url(r'^(?P<pk>[0-9]+)/input_sources/$', CredentialInputSourceSubList.as_view(), name='credential_input_source_sublist'),
    url(r'^(?P<pk>[0-9]+)/test/$', CredentialExternalTest.as_view(), name='credential_external_test'),
]

__all__ = ['urls']
