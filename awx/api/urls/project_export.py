# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    ProjectExportList,
    ProjectExportDetail,
    ProjectExportCancel,
    ProjectExportStdout,
    ProjectExportNotificationsList,
    ProjectExportEventsList,
)


urls = [
    url(r'^$', ProjectExportList.as_view(), name='project_export_list'),
    url(r'^(?P<pk>[0-9]+)/$', ProjectExportDetail.as_view(), name='project_export_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$', ProjectExportCancel.as_view(), name='project_export_cancel'),
    url(r'^(?P<pk>[0-9]+)/stdout/$', ProjectExportStdout.as_view(), name='project_export_stdout'),
    url(r'^(?P<pk>[0-9]+)/notifications/$', ProjectExportNotificationsList.as_view(), name='project_export_notifications_list'),
    url(r'^(?P<pk>[0-9]+)/events/$', ProjectExportEventsList.as_view(), name='project_export_events_list'),
]

__all__ = ['urls']
