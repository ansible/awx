from django.conf.urls import url

from awx.api.views import (
    ExecutionEnvironmentList,
    ExecutionEnvironmentDetail,
)


urls = [
    url(r'^$', ExecutionEnvironmentList.as_view(), name='execution_environment_list'),
    url(r'^(?P<pk>[0-9]+)/$', ExecutionEnvironmentDetail.as_view(), name='execution_environment_detail'),
]

__all__ = ['urls']
