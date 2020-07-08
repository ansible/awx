from django.conf.urls import url

from awx.api.views import (
    ExecutionEnvironmentList,
    ExecutionEnvironmentDetail,
    ExecutionEnvironmentJobTemplateList,
    ExecutionEnvironmentActivityStreamList,
)


urls = [
    url(r'^$', ExecutionEnvironmentList.as_view(), name='execution_environment_list'),
    url(r'^(?P<pk>[0-9]+)/$', ExecutionEnvironmentDetail.as_view(), name='execution_environment_detail'),
    url(r'^(?P<pk>[0-9]+)/unified_job_templates/$', ExecutionEnvironmentJobTemplateList.as_view(), name='execution_environment_job_template_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$', ExecutionEnvironmentActivityStreamList.as_view(), name='execution_environment_activity_stream_list'),
]

__all__ = ['urls']
