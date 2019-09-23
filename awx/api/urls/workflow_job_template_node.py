# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

from awx.api.views import (
    WorkflowJobTemplateNodeList,
    WorkflowJobTemplateNodeDetail,
    WorkflowJobTemplateNodeSuccessNodesList,
    WorkflowJobTemplateNodeFailureNodesList,
    WorkflowJobTemplateNodeAlwaysNodesList,
    WorkflowJobTemplateNodeCredentialsList,
    WorkflowJobTemplateNodeCreateApproval,
)


urls = [
    url(r'^$', WorkflowJobTemplateNodeList.as_view(), name='workflow_job_template_node_list'),
    url(r'^(?P<pk>[0-9]+)/$', WorkflowJobTemplateNodeDetail.as_view(), name='workflow_job_template_node_detail'),
    url(r'^(?P<pk>[0-9]+)/success_nodes/$', WorkflowJobTemplateNodeSuccessNodesList.as_view(), name='workflow_job_template_node_success_nodes_list'),
    url(r'^(?P<pk>[0-9]+)/failure_nodes/$', WorkflowJobTemplateNodeFailureNodesList.as_view(), name='workflow_job_template_node_failure_nodes_list'),
    url(r'^(?P<pk>[0-9]+)/always_nodes/$', WorkflowJobTemplateNodeAlwaysNodesList.as_view(), name='workflow_job_template_node_always_nodes_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$', WorkflowJobTemplateNodeCredentialsList.as_view(), name='workflow_job_template_node_credentials_list'),
    url(r'^(?P<pk>[0-9]+)/create_approval_template/$', WorkflowJobTemplateNodeCreateApproval.as_view(), name='workflow_job_template_node_create_approval'),
]

__all__ = ['urls']
