# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    TeamList,
    TeamDetail,
    TeamProjectsList,
    TeamUsersList,
    TeamCredentialsList,
    TeamRolesList,
    TeamObjectRolesList,
    TeamActivityStreamList,
    TeamAccessList,
)


urls = [
    url(r'^$', TeamList.as_view(), name='team_list'),
    url(r'^(?P<pk>[0-9]+)/$', TeamDetail.as_view(), name='team_detail'),
    url(r'^(?P<pk>[0-9]+)/projects/$', TeamProjectsList.as_view(), name='team_projects_list'),
    url(r'^(?P<pk>[0-9]+)/users/$', TeamUsersList.as_view(), name='team_users_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$', TeamCredentialsList.as_view(), name='team_credentials_list'),
    url(r'^(?P<pk>[0-9]+)/roles/$', TeamRolesList.as_view(), name='team_roles_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$', TeamObjectRolesList.as_view(), name='team_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$', TeamActivityStreamList.as_view(), name='team_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$', TeamAccessList.as_view(), name='team_access_list'),
]

__all__ = ['urls']
