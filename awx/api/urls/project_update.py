# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    ProjectUpdateList,
    ProjectUpdateDetail,
    ProjectUpdateCancel,
    ProjectUpdateStdout,
    ProjectUpdateScmInventoryUpdates,
    ProjectUpdateNotificationsList,
    ProjectUpdateEventsList,
)


urls = [
    re_path(r'^$', ProjectUpdateList.as_view(), name='project_update_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', ProjectUpdateDetail.as_view(), name='project_update_detail'),
    re_path(r'^(?P<pk>[0-9]+)/cancel/$', ProjectUpdateCancel.as_view(), name='project_update_cancel'),
    re_path(r'^(?P<pk>[0-9]+)/stdout/$', ProjectUpdateStdout.as_view(), name='project_update_stdout'),
    re_path(r'^(?P<pk>[0-9]+)/scm_inventory_updates/$', ProjectUpdateScmInventoryUpdates.as_view(), name='project_update_scm_inventory_updates'),
    re_path(r'^(?P<pk>[0-9]+)/notifications/$', ProjectUpdateNotificationsList.as_view(), name='project_update_notifications_list'),
    re_path(r'^(?P<pk>[0-9]+)/events/$', ProjectUpdateEventsList.as_view(), name='project_update_events_list'),
]

__all__ = ['urls']
