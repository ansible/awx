# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    UserList,
    UserDetail,
    UserTeamsList,
    UserOrganizationsList,
    UserAdminOfOrganizationsList,
    UserProjectsList,
    UserCredentialsList,
    UserRolesList,
    UserActivityStreamList,
    UserAccessList,
    OAuth2ApplicationList,
    OAuth2UserTokenList,
    UserPersonalTokenList,
    UserAuthorizedTokenList,
)

urls = [
    re_path(r'^$', UserList.as_view(), name='user_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', UserDetail.as_view(), name='user_detail'),
    re_path(r'^(?P<pk>[0-9]+)/teams/$', UserTeamsList.as_view(), name='user_teams_list'),
    re_path(r'^(?P<pk>[0-9]+)/organizations/$', UserOrganizationsList.as_view(), name='user_organizations_list'),
    re_path(r'^(?P<pk>[0-9]+)/admin_of_organizations/$', UserAdminOfOrganizationsList.as_view(), name='user_admin_of_organizations_list'),
    re_path(r'^(?P<pk>[0-9]+)/projects/$', UserProjectsList.as_view(), name='user_projects_list'),
    re_path(r'^(?P<pk>[0-9]+)/credentials/$', UserCredentialsList.as_view(), name='user_credentials_list'),
    re_path(r'^(?P<pk>[0-9]+)/roles/$', UserRolesList.as_view(), name='user_roles_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', UserActivityStreamList.as_view(), name='user_activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/access_list/$', UserAccessList.as_view(), name='user_access_list'),
    re_path(r'^(?P<pk>[0-9]+)/applications/$', OAuth2ApplicationList.as_view(), name='o_auth2_application_list'),
    re_path(r'^(?P<pk>[0-9]+)/tokens/$', OAuth2UserTokenList.as_view(), name='o_auth2_token_list'),
    re_path(r'^(?P<pk>[0-9]+)/authorized_tokens/$', UserAuthorizedTokenList.as_view(), name='user_authorized_token_list'),
    re_path(r'^(?P<pk>[0-9]+)/personal_tokens/$', UserPersonalTokenList.as_view(), name='user_personal_token_list'),
]

__all__ = ['urls']
