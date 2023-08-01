from django.urls import re_path

from awx.api.views import (
    DashboardView,
    DashboardJobsGraphView,
)


extend_urls = [
    re_path(r'^dashboard/$', DashboardView.as_view(), name='dashboard_view'),
    re_path(r'^dashboard/graphs/jobs/$', DashboardJobsGraphView.as_view(), name='dashboard_jobs_graph_view'),
]
