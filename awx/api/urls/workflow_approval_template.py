# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    WorfklowApprovalTemplateList,
    WorfklowApprovalTemplateDetail,
    WorkflowApprovalTemplateJobsList,
    WorkflowApprovalTemplateNotificationTemplatesErrorList,
    WorkflowApprovalTemplateNotificationTemplatesStartedList,
    WorkflowApprovalTemplateNotificationTemplatesSuccessList,
)


urls = [
    url(r'^$', WorfklowApprovalTemplateList.as_view(), name='workflow_approval_template_list'),
    url(r'^(?P<pk>[0-9]+)/$', WorfklowApprovalTemplateDetail.as_view(), name='workflow_approval_template_detail'),
    url(r'^(?P<pk>[0-9]+)/approvals/$', WorkflowApprovalTemplateJobsList.as_view(), name='workflow_approval_template_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_started/$', WorkflowApprovalTemplateNotificationTemplatesStartedList.as_view(),
        name='workflow_approval_template_notification_templates_started_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$', WorkflowApprovalTemplateNotificationTemplatesErrorList.as_view(),
        name='workflow_approval_template_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$', WorkflowApprovalTemplateNotificationTemplatesSuccessList.as_view(),
        name='workflow_approval_template_notification_templates_success_list'),
]

__all__ = ['urls']
