# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    WorkflowApprovalList,
    WorkflowApprovalDetail,
    WorkflowApprovalNotificationsList,
)


urls = [
    url(r'^$', WorkflowApprovalList.as_view(), name='workflow_approval_list'),
    url(r'^(?P<pk>[0-9]+)/$', WorkflowApprovalDetail.as_view(), name='workflow_approval_detail'),
    url(r'^(?P<pk>[0-9]+)/approve/$', WorkflowApprovalDetail.as_view(), name='approved_workflow'),
    url(r'^(?P<pk>[0-9]+)/reject/$', WorkflowApprovalDetail.as_view(), name='rejected_workflow'),
    url(r'^(?P<pk>[0-9]+)/notifications/$', WorkflowApprovalNotificationsList.as_view(), name='workflow_approval_notifications_list'),
]

__all__ = ['urls']
