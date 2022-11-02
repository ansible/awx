# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import WorkflowApprovalList, WorkflowApprovalDetail, WorkflowApprovalApprove, WorkflowApprovalDeny


urls = [
    re_path(r'^$', WorkflowApprovalList.as_view(), name='workflow_approval_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', WorkflowApprovalDetail.as_view(), name='workflow_approval_detail'),
    re_path(r'^(?P<pk>[0-9]+)/approve/$', WorkflowApprovalApprove.as_view(), name='workflow_approval_approve'),
    re_path(r'^(?P<pk>[0-9]+)/deny/$', WorkflowApprovalDeny.as_view(), name='workflow_approval_deny'),
]

__all__ = ['urls']
