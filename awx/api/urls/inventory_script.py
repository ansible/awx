# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    InventoryScriptList,
    InventoryScriptDetail,
    InventoryScriptObjectRolesList,
    InventoryScriptCopy,
)


urls = [
    url(r'^$', InventoryScriptList.as_view(), name='inventory_script_list'),
    url(r'^(?P<pk>[0-9]+)/$', InventoryScriptDetail.as_view(), name='inventory_script_detail'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$', InventoryScriptObjectRolesList.as_view(), name='inventory_script_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/copy/$', InventoryScriptCopy.as_view(), name='inventory_script_copy'),
]

__all__ = ['urls']
