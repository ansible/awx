# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    InventorySourceList,
    InventorySourceDetail,
    InventorySourceUpdateView,
    InventorySourceUpdatesList,
    InventorySourceActivityStreamList,
    InventorySourceSchedulesList,
    InventorySourceCredentialsList,
    InventorySourceGroupsList,
    InventorySourceHostsList,
    InventorySourceNotificationTemplatesErrorList,
    InventorySourceNotificationTemplatesStartedList,
    InventorySourceNotificationTemplatesSuccessList,
)


urls = [
    url(r'^$', InventorySourceList.as_view(), name='inventory_source_list'),
    url(r'^(?P<pk>[0-9]+)/$', InventorySourceDetail.as_view(), name='inventory_source_detail'),
    url(r'^(?P<pk>[0-9]+)/update/$', InventorySourceUpdateView.as_view(), name='inventory_source_update_view'),
    url(r'^(?P<pk>[0-9]+)/inventory_updates/$', InventorySourceUpdatesList.as_view(), name='inventory_source_updates_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$', InventorySourceActivityStreamList.as_view(), name='inventory_source_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/schedules/$', InventorySourceSchedulesList.as_view(), name='inventory_source_schedules_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$', InventorySourceCredentialsList.as_view(), name='inventory_source_credentials_list'),
    url(r'^(?P<pk>[0-9]+)/groups/$', InventorySourceGroupsList.as_view(), name='inventory_source_groups_list'),
    url(r'^(?P<pk>[0-9]+)/hosts/$', InventorySourceHostsList.as_view(), name='inventory_source_hosts_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_started/$', InventorySourceNotificationTemplatesStartedList.as_view(),
        name='inventory_source_notification_templates_started_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$', InventorySourceNotificationTemplatesErrorList.as_view(),
        name='inventory_source_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$', InventorySourceNotificationTemplatesSuccessList.as_view(),
        name='inventory_source_notification_templates_success_list'),
]

__all__ = ['urls']
