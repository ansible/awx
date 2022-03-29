# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    HostList,
    HostDetail,
    HostVariableData,
    HostGroupsList,
    HostAllGroupsList,
    HostJobEventsList,
    HostJobHostSummariesList,
    HostActivityStreamList,
    HostInventorySourcesList,
    HostSmartInventoriesList,
    HostAdHocCommandsList,
    HostAdHocCommandEventsList,
)


urls = [
    re_path(r'^$', HostList.as_view(), name='host_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', HostDetail.as_view(), name='host_detail'),
    re_path(r'^(?P<pk>[0-9]+)/variable_data/$', HostVariableData.as_view(), name='host_variable_data'),
    re_path(r'^(?P<pk>[0-9]+)/groups/$', HostGroupsList.as_view(), name='host_groups_list'),
    re_path(r'^(?P<pk>[0-9]+)/all_groups/$', HostAllGroupsList.as_view(), name='host_all_groups_list'),
    re_path(r'^(?P<pk>[0-9]+)/job_events/', HostJobEventsList.as_view(), name='host_job_events_list'),
    re_path(r'^(?P<pk>[0-9]+)/job_host_summaries/$', HostJobHostSummariesList.as_view(), name='host_job_host_summaries_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', HostActivityStreamList.as_view(), name='host_activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/inventory_sources/$', HostInventorySourcesList.as_view(), name='host_inventory_sources_list'),
    re_path(r'^(?P<pk>[0-9]+)/smart_inventories/$', HostSmartInventoriesList.as_view(), name='host_smart_inventories_list'),
    re_path(r'^(?P<pk>[0-9]+)/ad_hoc_commands/$', HostAdHocCommandsList.as_view(), name='host_ad_hoc_commands_list'),
    re_path(r'^(?P<pk>[0-9]+)/ad_hoc_command_events/$', HostAdHocCommandEventsList.as_view(), name='host_ad_hoc_command_events_list'),
]

__all__ = ['urls']
