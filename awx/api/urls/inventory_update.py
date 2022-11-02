# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views.inventory import (
    InventoryUpdateEventsList,
)
from awx.api.views import (
    InventoryUpdateList,
    InventoryUpdateDetail,
    InventoryUpdateCancel,
    InventoryUpdateStdout,
    InventoryUpdateNotificationsList,
    InventoryUpdateCredentialsList,
)


urls = [
    re_path(r'^$', InventoryUpdateList.as_view(), name='inventory_update_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', InventoryUpdateDetail.as_view(), name='inventory_update_detail'),
    re_path(r'^(?P<pk>[0-9]+)/cancel/$', InventoryUpdateCancel.as_view(), name='inventory_update_cancel'),
    re_path(r'^(?P<pk>[0-9]+)/stdout/$', InventoryUpdateStdout.as_view(), name='inventory_update_stdout'),
    re_path(r'^(?P<pk>[0-9]+)/notifications/$', InventoryUpdateNotificationsList.as_view(), name='inventory_update_notifications_list'),
    re_path(r'^(?P<pk>[0-9]+)/credentials/$', InventoryUpdateCredentialsList.as_view(), name='inventory_update_credentials_list'),
    re_path(r'^(?P<pk>[0-9]+)/events/$', InventoryUpdateEventsList.as_view(), name='inventory_update_events_list'),
]

__all__ = ['urls']
