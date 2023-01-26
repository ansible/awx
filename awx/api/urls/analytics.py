# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views.analytics import AnalyticsRootView, AnalyticsTestList, AnalyticsReportsList, AnalyticsReportOptionsList

urls = [
    re_path(r'^$', AnalyticsRootView.as_view(), name='analytics_root_view'),
    re_path(r'^test/$', AnalyticsTestList.as_view(), name='analytics_test_list'),
    re_path(r'^reports/$', AnalyticsReportsList.as_view(), name='analytics_reports_list'),
    re_path(r'^report_options/$', AnalyticsReportOptionsList.as_view(), name='analytics_report_options_list'),
]

__all__ = ['urls']
