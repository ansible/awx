from django.urls import re_path

from awx.api.views.bulk import (
    BulkView,
    BulkHostCreateView,
    BulkJobLaunchView,
)


extend_urls = [
    re_path(r'^bulk/$', BulkView.as_view(), name='bulk'),
    re_path(r'^bulk/host_create/$', BulkHostCreateView.as_view(), name='bulk_host_create'),
    re_path(r'^bulk/job_launch/$', BulkJobLaunchView.as_view(), name='bulk_job_launch'),
]
