# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    GroupList,
    GroupDetail,
    GroupChildrenList,
    GroupHostsList,
    GroupAllHostsList,
    GroupVariableData,
    GroupJobEventsList,
    GroupJobHostSummariesList,
    GroupPotentialChildrenList,
    GroupActivityStreamList,
    GroupInventorySourcesList,
    GroupAdHocCommandsList,
)


urls = [
    re_path(r'^$', GroupList.as_view(), name='group_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', GroupDetail.as_view(), name='group_detail'),
    re_path(r'^(?P<pk>[0-9]+)/children/$', GroupChildrenList.as_view(), name='group_children_list'),
    re_path(r'^(?P<pk>[0-9]+)/hosts/$', GroupHostsList.as_view(), name='group_hosts_list'),
    re_path(r'^(?P<pk>[0-9]+)/all_hosts/$', GroupAllHostsList.as_view(), name='group_all_hosts_list'),
    re_path(r'^(?P<pk>[0-9]+)/variable_data/$', GroupVariableData.as_view(), name='group_variable_data'),
    re_path(r'^(?P<pk>[0-9]+)/job_events/$', GroupJobEventsList.as_view(), name='group_job_events_list'),
    re_path(r'^(?P<pk>[0-9]+)/job_host_summaries/$', GroupJobHostSummariesList.as_view(), name='group_job_host_summaries_list'),
    re_path(r'^(?P<pk>[0-9]+)/potential_children/$', GroupPotentialChildrenList.as_view(), name='group_potential_children_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', GroupActivityStreamList.as_view(), name='group_activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/inventory_sources/$', GroupInventorySourcesList.as_view(), name='group_inventory_sources_list'),
    re_path(r'^(?P<pk>[0-9]+)/ad_hoc_commands/$', GroupAdHocCommandsList.as_view(), name='group_ad_hoc_commands_list'),
]

__all__ = ['urls']
