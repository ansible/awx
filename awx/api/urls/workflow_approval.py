# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    WorkflowApprovalList,
    WorkflowApprovalDetail,
    WorkflowApprovalApprove,
    WorkflowApprovalDeny,
    WorkflowApprovalNotificationsList,
)


urls = [
    url(r'^$', WorkflowApprovalList.as_view(), name='workflow_approval_list'),
    url(r'^(?P<pk>[0-9]+)/$', WorkflowApprovalDetail.as_view(), name='workflow_approval_detail'),
    url(r'^(?P<pk>[0-9]+)/approve/$', WorkflowApprovalApprove.as_view(), name='workflow_approval_approve'),
    url(r'^(?P<pk>[0-9]+)/deny/$', WorkflowApprovalDeny.as_view(), name='workflow_approval_deny'),
    url(r'^(?P<pk>[0-9]+)/notifications/$', WorkflowApprovalNotificationsList.as_view(), name='workflow_approval_notifications_list'),
]

__all__ = ['urls']
