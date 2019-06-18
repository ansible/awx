# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    ProjectList,
    ProjectDetail,
    ProjectPlaybooks,
    ProjectInventories,
    ProjectScmInventorySources,
    ProjectTeamsList,
    ProjectUpdateView,
    ProjectUpdatesList,
    ProjectActivityStreamList,
    ProjectSchedulesList,
    ProjectNotificationTemplatesErrorList,
    ProjectNotificationTemplatesStartedList,
    ProjectNotificationTemplatesSuccessList,
    ProjectObjectRolesList,
    ProjectAccessList,
    ProjectCopy,
)


urls = [
    url(r'^$', ProjectList.as_view(), name='project_list'),
    url(r'^(?P<pk>[0-9]+)/$', ProjectDetail.as_view(), name='project_detail'),
    url(r'^(?P<pk>[0-9]+)/playbooks/$', ProjectPlaybooks.as_view(), name='project_playbooks'),
    url(r'^(?P<pk>[0-9]+)/inventories/$', ProjectInventories.as_view(), name='project_inventories'),
    url(r'^(?P<pk>[0-9]+)/scm_inventory_sources/$', ProjectScmInventorySources.as_view(), name='project_scm_inventory_sources'),
    url(r'^(?P<pk>[0-9]+)/teams/$', ProjectTeamsList.as_view(), name='project_teams_list'),
    url(r'^(?P<pk>[0-9]+)/update/$', ProjectUpdateView.as_view(), name='project_update_view'),
    url(r'^(?P<pk>[0-9]+)/project_updates/$', ProjectUpdatesList.as_view(), name='project_updates_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$', ProjectActivityStreamList.as_view(), name='project_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/schedules/$', ProjectSchedulesList.as_view(), name='project_schedules_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$', ProjectNotificationTemplatesErrorList.as_view(), name='project_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$', ProjectNotificationTemplatesSuccessList.as_view(),
        name='project_notification_templates_success_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_started/$', ProjectNotificationTemplatesStartedList.as_view(),
        name='project_notification_templates_started_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$', ProjectObjectRolesList.as_view(), name='project_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$', ProjectAccessList.as_view(), name='project_access_list'),
    url(r'^(?P<pk>[0-9]+)/copy/$', ProjectCopy.as_view(), name='project_copy'),
]

__all__ = ['urls']
