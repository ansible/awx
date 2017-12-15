# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

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
    url(r'^$', ProjectUpdateList.as_view(), name='project_update_list'),
    url(r'^(?P<pk>[0-9]+)/$', ProjectUpdateDetail.as_view(), name='project_update_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$', ProjectUpdateCancel.as_view(), name='project_update_cancel'),
    url(r'^(?P<pk>[0-9]+)/stdout/$', ProjectUpdateStdout.as_view(), name='project_update_stdout'),
    url(r'^(?P<pk>[0-9]+)/scm_inventory_updates/$', ProjectUpdateScmInventoryUpdates.as_view(), name='project_update_scm_inventory_updates'),
    url(r'^(?P<pk>[0-9]+)/notifications/$', ProjectUpdateNotificationsList.as_view(), name='project_update_notifications_list'),
    url(r'^(?P<pk>[0-9]+)/events/$', ProjectUpdateEventsList.as_view(), name='project_update_events_list'),
]

__all__ = ['urls']
