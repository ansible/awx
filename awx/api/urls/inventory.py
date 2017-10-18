# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    InventoryList,
    InventoryDetail,
    InventoryHostsList,
    InventoryGroupsList,
    InventoryRootGroupsList,
    InventoryVariableData,
    InventoryScriptView,
    InventoryTreeView,
    InventoryInventorySourcesList,
    InventoryInventorySourcesUpdate,
    InventoryActivityStreamList,
    InventoryJobTemplateList,
    InventoryAdHocCommandsList,
    InventoryAccessList,
    InventoryObjectRolesList,
    InventoryInstanceGroupsList,
    InventoryCopy,
)


urls = [
    url(r'^$', InventoryList.as_view(), name='inventory_list'),
    url(r'^(?P<pk>[0-9]+)/$', InventoryDetail.as_view(), name='inventory_detail'),
    url(r'^(?P<pk>[0-9]+)/hosts/$', InventoryHostsList.as_view(), name='inventory_hosts_list'),
    url(r'^(?P<pk>[0-9]+)/groups/$', InventoryGroupsList.as_view(), name='inventory_groups_list'),
    url(r'^(?P<pk>[0-9]+)/root_groups/$', InventoryRootGroupsList.as_view(), name='inventory_root_groups_list'),
    url(r'^(?P<pk>[0-9]+)/variable_data/$', InventoryVariableData.as_view(), name='inventory_variable_data'),
    url(r'^(?P<pk>[0-9]+)/script/$', InventoryScriptView.as_view(), name='inventory_script_view'),
    url(r'^(?P<pk>[0-9]+)/tree/$', InventoryTreeView.as_view(), name='inventory_tree_view'),
    url(r'^(?P<pk>[0-9]+)/inventory_sources/$', InventoryInventorySourcesList.as_view(), name='inventory_inventory_sources_list'),
    url(r'^(?P<pk>[0-9]+)/update_inventory_sources/$', InventoryInventorySourcesUpdate.as_view(), name='inventory_inventory_sources_update'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$', InventoryActivityStreamList.as_view(), name='inventory_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/job_templates/$', InventoryJobTemplateList.as_view(), name='inventory_job_template_list'),
    url(r'^(?P<pk>[0-9]+)/ad_hoc_commands/$', InventoryAdHocCommandsList.as_view(), name='inventory_ad_hoc_commands_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$', InventoryAccessList.as_view(), name='inventory_access_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$', InventoryObjectRolesList.as_view(), name='inventory_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/instance_groups/$', InventoryInstanceGroupsList.as_view(), name='inventory_instance_groups_list'),
    url(r'^(?P<pk>[0-9]+)/copy/$', InventoryCopy.as_view(), name='inventory_copy'),
]

__all__ = ['urls']
