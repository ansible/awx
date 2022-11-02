from django.urls import re_path

from awx.api.views import (
    ExecutionEnvironmentList,
    ExecutionEnvironmentDetail,
    ExecutionEnvironmentJobTemplateList,
    ExecutionEnvironmentCopy,
    ExecutionEnvironmentActivityStreamList,
)


urls = [
    re_path(r'^$', ExecutionEnvironmentList.as_view(), name='execution_environment_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', ExecutionEnvironmentDetail.as_view(), name='execution_environment_detail'),
    re_path(r'^(?P<pk>[0-9]+)/unified_job_templates/$', ExecutionEnvironmentJobTemplateList.as_view(), name='execution_environment_job_template_list'),
    re_path(r'^(?P<pk>[0-9]+)/copy/$', ExecutionEnvironmentCopy.as_view(), name='execution_environment_copy'),
    re_path(r'^(?P<pk>[0-9]+)/activity_stream/$', ExecutionEnvironmentActivityStreamList.as_view(), name='execution_environment_activity_stream_list'),
]

__all__ = ['urls']
