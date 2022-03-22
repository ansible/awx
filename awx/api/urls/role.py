# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import RoleList, RoleDetail, RoleUsersList, RoleTeamsList, RoleParentsList, RoleChildrenList


urls = [
    re_path(r'^$', RoleList.as_view(), name='role_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', RoleDetail.as_view(), name='role_detail'),
    re_path(r'^(?P<pk>[0-9]+)/users/$', RoleUsersList.as_view(), name='role_users_list'),
    re_path(r'^(?P<pk>[0-9]+)/teams/$', RoleTeamsList.as_view(), name='role_teams_list'),
    re_path(r'^(?P<pk>[0-9]+)/parents/$', RoleParentsList.as_view(), name='role_parents_list'),
    re_path(r'^(?P<pk>[0-9]+)/children/$', RoleChildrenList.as_view(), name='role_children_list'),
]

__all__ = ['urls']
