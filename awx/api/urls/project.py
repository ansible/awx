# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

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
    re_path(r'^$', ProjectList.as_view(), name='project_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', ProjectDetail.as_view(), name='project_detail'),
    re_path(r'^(?P<pk>[0-9]+)/playbooks/$', ProjectPlaybooks.as_view(), name='project_playbooks'),
    re_path(r'^(?P<pk>[0-9]+)/inventories/$', ProjectInventories.as_view(), name='project_inventories'),
    re_path(r'^(?P<pk>[0-9]+)/scm_inventory_sources/$', ProjectScmInventorySources.as_view(), name='project_scm_inventory_sources'),
    re_path(r'^(?P<pk>[0-9]+)/teams/$', ProjectTeamsList.as_view(), name='project_teams_list'),
    re_path(r'^(?P<pk>[0-9]+)/update/$', ProjectUpdateView.as_view(), name='project_update_view'),
    re_path(r'^(?P<pk>[0-9]+)/project_updates/$', ProjectUpdatesList.as_view(), name='project_updates_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', ProjectActivityStreamList.as_view(), name='project_activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/schedules/$', ProjectSchedulesList.as_view(), name='project_schedules_list'),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_error/$', ProjectNotificationTemplatesErrorList.as_view(), name='project_notification_templates_error_list'
    ),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_success/$',
        ProjectNotificationTemplatesSuccessList.as_view(),
        name='project_notification_templates_success_list',
    ),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_started/$',
        ProjectNotificationTemplatesStartedList.as_view(),
        name='project_notification_templates_started_list',
    ),
    re_path(r'^(?P<pk>[0-9]+)/object_roles/$', ProjectObjectRolesList.as_view(), name='project_object_roles_list'),
    re_path(r'^(?P<pk>[0-9]+)/access_list/$', ProjectAccessList.as_view(), name='project_access_list'),
    re_path(r'^(?P<pk>[0-9]+)/copy/$', ProjectCopy.as_view(), name='project_copy'),
]

__all__ = ['urls']
