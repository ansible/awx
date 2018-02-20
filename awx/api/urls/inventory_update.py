# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    InventoryUpdateList,
    InventoryUpdateDetail,
    InventoryUpdateCancel,
    InventoryUpdateStdout,
    InventoryUpdateNotificationsList,
    InventoryUpdateCredentialsList,
    InventoryUpdateEventsList,
)


urls = [
    url(r'^$', InventoryUpdateList.as_view(), name='inventory_update_list'),
    url(r'^(?P<pk>[0-9]+)/$', InventoryUpdateDetail.as_view(), name='inventory_update_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$', InventoryUpdateCancel.as_view(), name='inventory_update_cancel'),
    url(r'^(?P<pk>[0-9]+)/stdout/$', InventoryUpdateStdout.as_view(), name='inventory_update_stdout'),
    url(r'^(?P<pk>[0-9]+)/notifications/$', InventoryUpdateNotificationsList.as_view(), name='inventory_update_notifications_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$', InventoryUpdateCredentialsList.as_view(), name='inventory_update_credentials_list'),
    url(r'^(?P<pk>[0-9]+)/events/$', InventoryUpdateEventsList.as_view(), name='inventory_update_events_list'),
]

__all__ = ['urls']
