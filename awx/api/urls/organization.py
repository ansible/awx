# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    OrganizationList,
    OrganizationDetail,
    OrganizationUsersList,
    OrganizationAdminsList,
    OrganizationInventoriesList,
    OrganizationExecutionEnvironmentsList,
    OrganizationProjectsList,
    OrganizationJobTemplatesList,
    OrganizationWorkflowJobTemplatesList,
    OrganizationTeamsList,
    OrganizationCredentialList,
    OrganizationActivityStreamList,
    OrganizationNotificationTemplatesList,
    OrganizationNotificationTemplatesErrorList,
    OrganizationNotificationTemplatesStartedList,
    OrganizationNotificationTemplatesSuccessList,
    OrganizationNotificationTemplatesApprovalList,
    OrganizationInstanceGroupsList,
    OrganizationGalaxyCredentialsList,
    OrganizationObjectRolesList,
    OrganizationAccessList,
    OrganizationApplicationList,
)


urls = [
    re_path(r'^$', OrganizationList.as_view(), name='organization_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', OrganizationDetail.as_view(), name='organization_detail'),
    re_path(r'^(?P<pk>[0-9]+)/users/$', OrganizationUsersList.as_view(), name='organization_users_list'),
    re_path(r'^(?P<pk>[0-9]+)/admins/$', OrganizationAdminsList.as_view(), name='organization_admins_list'),
    re_path(r'^(?P<pk>[0-9]+)/inventories/$', OrganizationInventoriesList.as_view(), name='organization_inventories_list'),
    re_path(r'^(?P<pk>[0-9]+)/execution_environments/$', OrganizationExecutionEnvironmentsList.as_view(), name='organization_execution_environments_list'),
    re_path(r'^(?P<pk>[0-9]+)/projects/$', OrganizationProjectsList.as_view(), name='organization_projects_list'),
    re_path(r'^(?P<pk>[0-9]+)/job_templates/$', OrganizationJobTemplatesList.as_view(), name='organization_job_templates_list'),
    re_path(r'^(?P<pk>[0-9]+)/workflow_job_templates/$', OrganizationWorkflowJobTemplatesList.as_view(), name='organization_workflow_job_templates_list'),
    re_path(r'^(?P<pk>[0-9]+)/teams/$', OrganizationTeamsList.as_view(), name='organization_teams_list'),
    re_path(r'^(?P<pk>[0-9]+)/credentials/$', OrganizationCredentialList.as_view(), name='organization_credential_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', OrganizationActivityStreamList.as_view(), name='organization_activity_stream_list'),
    re_path(r'^(?P<pk>[0-9]+)/notification_templates/$', OrganizationNotificationTemplatesList.as_view(), name='organization_notification_templates_list'),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_started/$',
        OrganizationNotificationTemplatesStartedList.as_view(),
        name='organization_notification_templates_started_list',
    ),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_error/$',
        OrganizationNotificationTemplatesErrorList.as_view(),
        name='organization_notification_templates_error_list',
    ),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_success/$',
        OrganizationNotificationTemplatesSuccessList.as_view(),
        name='organization_notification_templates_success_list',
    ),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_approvals/$',
        OrganizationNotificationTemplatesApprovalList.as_view(),
        name='organization_notification_templates_approvals_list',
    ),
    re_path(r'^(?P<pk>[0-9]+)/instance_groups/$', OrganizationInstanceGroupsList.as_view(), name='organization_instance_groups_list'),
    re_path(r'^(?P<pk>[0-9]+)/galaxy_credentials/$', OrganizationGalaxyCredentialsList.as_view(), name='organization_galaxy_credentials_list'),
    re_path(r'^(?P<pk>[0-9]+)/object_roles/$', OrganizationObjectRolesList.as_view(), name='organization_object_roles_list'),
    re_path(r'^(?P<pk>[0-9]+)/access_list/$', OrganizationAccessList.as_view(), name='organization_access_list'),
    re_path(r'^(?P<pk>[0-9]+)/applications/$', OrganizationApplicationList.as_view(), name='organization_applications_list'),
]

__all__ = ['urls']
