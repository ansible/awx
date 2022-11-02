# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    WorkflowJobList,
    WorkflowJobDetail,
    WorkflowJobWorkflowNodesList,
    WorkflowJobLabelList,
    WorkflowJobCancel,
    WorkflowJobRelaunch,
    WorkflowJobNotificationsList,
    WorkflowJobActivityStreamList,
)


urls = [
    re_path(r'^$', WorkflowJobList.as_view(), name='workflow_job_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', WorkflowJobDetail.as_view(), name='workflow_job_detail'),
    re_path(r'^(?P<pk>[0-9]+)/workflow_nodes/$', WorkflowJobWorkflowNodesList.as_view(), name='workflow_job_workflow_nodes_list'),
    re_path(r'^(?P<pk>[0-9]+)/labels/$', WorkflowJobLabelList.as_view(), name='workflow_job_label_list'),
    re_path(r'^(?P<pk>[0-9]+)/cancel/$', WorkflowJobCancel.as_view(), name='workflow_job_cancel'),
    re_path(r'^(?P<pk>[0-9]+)/relaunch/$', WorkflowJobRelaunch.as_view(), name='workflow_job_relaunch'),
    re_path(r'^(?P<pk>[0-9]+)/notifications/$', WorkflowJobNotificationsList.as_view(), name='workflow_job_notifications_list'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', WorkflowJobActivityStreamList.as_view(), name='workflow_job_activity_stream_list'),
]

__all__ = ['urls']
