# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

"""URL routing configuration for workflow approval template API endpoints.

This module defines the URL patterns for accessing details, related jobs,
and attached notification templates for workflow approval nodes.
"""

from django.urls import re_path

from awx.api.views.workflow_approval_template import (
    WorkflowApprovalTemplateDetail,
    WorkflowApprovalTemplateJobsList,
    WorkflowApprovalTemplateNotificationTemplatesApprovalsList,
)

urls = [
    re_path(r'^(?P<pk>[0-9]+)/$', WorkflowApprovalTemplateDetail.as_view(), name='workflow_approval_template_detail'),
    re_path(r'^(?P<pk>[0-9]+)/approvals/$', WorkflowApprovalTemplateJobsList.as_view(), name='workflow_approval_template_jobs_list'),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_approvals/$',
        WorkflowApprovalTemplateNotificationTemplatesApprovalsList.as_view(),
        name='workflow_approval_template_notification_templates_approvals_list',
    ),
]
"""list[URLPattern]: URL patterns for workflow approval template sub-resources."""

__all__ = ['urls']