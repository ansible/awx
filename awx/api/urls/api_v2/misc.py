from django.urls import re_path, include

from awx.api.views.root import (
    ApiV2PingView,
)
from awx.api.views import (
    AuthView,
    UserMeList,
    UnifiedJobTemplateList,
    UnifiedJobList,
    OAuth2TokenList,
    HostMetricSummaryMonthlyList,
)
from awx.api.views.mesh_visualizer import MeshVisualizer
from awx.api.views.metrics import MetricsView


extend_urls = [
    re_path(r'^tokens/$', OAuth2TokenList.as_view(), name='o_auth2_token_list'),
    re_path(r'^metrics/$', MetricsView.as_view(), name='metrics_view'),
    re_path(r'^ping/$', ApiV2PingView.as_view(), name='api_v2_ping_view'),
    re_path(r'^auth/$', AuthView.as_view()),
    re_path(r'^me/$', UserMeList.as_view(), name='user_me_list'),
    re_path(r'^mesh_visualizer/', MeshVisualizer.as_view(), name='mesh_visualizer_view'),
    re_path(r'^settings/', include('awx.conf.urls')),
    re_path(r'^host_metric_summary_monthly/$', HostMetricSummaryMonthlyList.as_view(), name='host_metric_summary_monthly_list'),
    re_path(r'^unified_job_templates/$', UnifiedJobTemplateList.as_view(), name='unified_job_template_list'),
    re_path(r'^unified_jobs/$', UnifiedJobList.as_view(), name='unified_job_list'),
]
