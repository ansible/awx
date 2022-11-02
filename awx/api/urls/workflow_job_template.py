# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import include, re_path

from awx.api.views import (
    WorkflowJobTemplateList,
    WorkflowJobTemplateDetail,
    WorkflowJobTemplateJobsList,
    WorkflowJobTemplateLaunch,
    WorkflowJobTemplateCopy,
    WorkflowJobTemplateSchedulesList,
    WorkflowJobTemplateSurveySpec,
    WorkflowJobTemplateWorkflowNodesList,
    WorkflowJobTemplateActivityStreamList,
    WorkflowJobTemplateNotificationTemplatesErrorList,
    WorkflowJobTemplateNotificationTemplatesStartedList,
    WorkflowJobTemplateNotificationTemplatesSuccessList,
    WorkflowJobTemplateNotificationTemplatesApprovalList,
    WorkflowJobTemplateAccessList,
    WorkflowJobTemplateObjectRolesList,
    WorkflowJobTemplateLabelList,
)


urls = [
    re_path(r'^$', WorkflowJobTemplateList.as_view(), name='workflow_job_template_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', WorkflowJobTemplateDetail.as_view(), name='workflow_job_template_detail'),
    re_path(r'^(?P<pk>[0-9]+)/workflow_jobs/$', WorkflowJobTemplateJobsList.as_view(), name='workflow_job_template_jobs_list'),
    re_path(r'^(?P<pk>[0-9]+)/launch/$', WorkflowJobTemplateLaunch.as_view(), name='workflow_job_template_launch'),
    re_path(r'^(?P<pk>[0-9]+)/copy/$', WorkflowJobTemplateCopy.as_view(), name='workflow_job_template_copy'),
    re_path(r'^(?P<pk>[0-9]+)/schedules/$', WorkflowJobTemplateSchedulesList.as_view(), name='workflow_job_template_schedules_list'),
    re_path(r'^(?P<pk>[0-9]+)/survey_spec/$', WorkflowJobTemplateSurveySpec.as_view(), name='workflow_job_template_survey_spec'),
    re_path(r'^(?P<pk>[0-9]+)/workflow_nodes/$', WorkflowJobTemplateWorkflowNodesList.as_view(), name='workflow_job_template_workflow_nodes_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', WorkflowJobTemplateActivityStreamList.as_view(), name='workflow_job_template_activity_stream_list'),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_started/$',
        WorkflowJobTemplateNotificationTemplatesStartedList.as_view(),
        name='workflow_job_template_notification_templates_started_list',
    ),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_error/$',
        WorkflowJobTemplateNotificationTemplatesErrorList.as_view(),
        name='workflow_job_template_notification_templates_error_list',
    ),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_success/$',
        WorkflowJobTemplateNotificationTemplatesSuccessList.as_view(),
        name='workflow_job_template_notification_templates_success_list',
    ),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_approvals/$',
        WorkflowJobTemplateNotificationTemplatesApprovalList.as_view(),
        name='workflow_job_template_notification_templates_approvals_list',
    ),
    re_path(r'^(?P<pk>[0-9]+)/access_list/$', WorkflowJobTemplateAccessList.as_view(), name='workflow_job_template_access_list'),
    re_path(r'^(?P<pk>[0-9]+)/object_roles/$', WorkflowJobTemplateObjectRolesList.as_view(), name='workflow_job_template_object_roles_list'),
    re_path(r'^(?P<pk>[0-9]+)/labels/$', WorkflowJobTemplateLabelList.as_view(), name='workflow_job_template_label_list'),
    re_path(r'^(?P<pk>[0-9]+)/', include('awx.api.urls.webhooks'), {'model_kwarg': 'workflow_job_templates'}),
]

__all__ = ['urls']
