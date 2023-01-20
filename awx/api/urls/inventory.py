# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views.inventory import (
    InventoryList,
    InventoryDetail,
    ConstructedInventoryDetail,
    ConstructedInventoryList,
    InventoryActivityStreamList,
    InventorySourceInventoriesList,
    InventoryJobTemplateList,
    InventoryAccessList,
    InventoryObjectRolesList,
    InventoryInstanceGroupsList,
    InventoryLabelList,
    InventoryCopy,
)
from awx.api.views import (
    InventoryHostsList,
    InventoryGroupsList,
    InventoryInventorySourcesList,
    InventoryInventorySourcesUpdate,
    InventoryAdHocCommandsList,
    InventoryRootGroupsList,
    InventoryScriptView,
    InventoryTreeView,
    InventoryVariableData,
)


urls = [
    re_path(r'^$', InventoryList.as_view(), name='inventory_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', InventoryDetail.as_view(), name='inventory_detail'),
    re_path(r'^(?P<pk>[0-9]+)/hosts/$', InventoryHostsList.as_view(), name='inventory_hosts_list'),
    re_path(r'^(?P<pk>[0-9]+)/groups/$', InventoryGroupsList.as_view(), name='inventory_groups_list'),
    re_path(r'^(?P<pk>[0-9]+)/root_groups/$', InventoryRootGroupsList.as_view(), name='inventory_root_groups_list'),
    re_path(r'^(?P<pk>[0-9]+)/variable_data/$', InventoryVariableData.as_view(), name='inventory_variable_data'),
    re_path(r'^(?P<pk>[0-9]+)/script/$', InventoryScriptView.as_view(), name='inventory_script_view'),
    re_path(r'^(?P<pk>[0-9]+)/tree/$', InventoryTreeView.as_view(), name='inventory_tree_view'),
    re_path(r'^(?P<pk>[0-9]+)/inventory_sources/$', InventoryInventorySourcesList.as_view(), name='inventory_inventory_sources_list'),
    re_path(r'^(?P<pk>[0-9]+)/source_inventories/$', InventorySourceInventoriesList.as_view(), name='inventory_source_inventories'),
    re_path(r'^(?P<pk>[0-9]+)/update_inventory_sources/$', InventoryInventorySourcesUpdate.as_view(), name='inventory_inventory_sources_update'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', InventoryActivityStreamList.as_view(), name='inventory_activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/job_templates/$', InventoryJobTemplateList.as_view(), name='inventory_job_template_list'),
    re_path(r'^(?P<pk>[0-9]+)/ad_hoc_commands/$', InventoryAdHocCommandsList.as_view(), name='inventory_ad_hoc_commands_list'),
    re_path(r'^(?P<pk>[0-9]+)/access_list/$', InventoryAccessList.as_view(), name='inventory_access_list'),
    re_path(r'^(?P<pk>[0-9]+)/object_roles/$', InventoryObjectRolesList.as_view(), name='inventory_object_roles_list'),
    re_path(r'^(?P<pk>[0-9]+)/instance_groups/$', InventoryInstanceGroupsList.as_view(), name='inventory_instance_groups_list'),
    re_path(r'^(?P<pk>[0-9]+)/labels/$', InventoryLabelList.as_view(), name='inventory_label_list'),
    re_path(r'^(?P<pk>[0-9]+)/copy/$', InventoryCopy.as_view(), name='inventory_copy'),
]

# Constructed inventory special views
constructed_inventory_urls = [
    re_path(r'^$', ConstructedInventoryList.as_view(), name='constructed_inventory_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', ConstructedInventoryDetail.as_view(), name='constructed_inventory_detail'),
]

__all__ = ['urls', 'constructed_inventory_urls']
