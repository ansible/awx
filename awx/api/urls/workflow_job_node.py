# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    WorkflowJobNodeList,
    WorkflowJobNodeDetail,
    WorkflowJobNodeSuccessNodesList,
    WorkflowJobNodeFailureNodesList,
    WorkflowJobNodeAlwaysNodesList,
    WorkflowJobNodeCredentialsList,
)


urls = [
    re_path(r'^$', WorkflowJobNodeList.as_view(), name='workflow_job_node_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', WorkflowJobNodeDetail.as_view(), name='workflow_job_node_detail'),
    re_path(r'^(?P<pk>[0-9]+)/success_nodes/$', WorkflowJobNodeSuccessNodesList.as_view(), name='workflow_job_node_success_nodes_list'),
    re_path(r'^(?P<pk>[0-9]+)/failure_nodes/$', WorkflowJobNodeFailureNodesList.as_view(), name='workflow_job_node_failure_nodes_list'),
    re_path(r'^(?P<pk>[0-9]+)/always_nodes/$', WorkflowJobNodeAlwaysNodesList.as_view(), name='workflow_job_node_always_nodes_list'),
    re_path(r'^(?P<pk>[0-9]+)/credentials/$', WorkflowJobNodeCredentialsList.as_view(), name='workflow_job_node_credentials_list'),
]

__all__ = ['urls']
