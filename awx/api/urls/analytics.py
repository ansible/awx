# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

import awx.api.views.analytics as analytics


urls = [
    re_path(r'^$', analytics.AnalyticsRootView.as_view(), name='analytics_root_view'),
    re_path(r'^authorized/$', analytics.AnalyticsAuthorizedView.as_view(), name='analytics_authorized'),
    re_path(r'^reports/$', analytics.AnalyticsReportsList.as_view(), name='analytics_reports_list'),
    re_path(r'^report/(?P<slug>[\w-]+)/$', analytics.AnalyticsReportDetail.as_view(), name='analytics_report_detail'),
    re_path(r'^report_options/$', analytics.AnalyticsReportOptionsList.as_view(), name='analytics_report_options_list'),
    re_path(r'^adoption_rate/$', analytics.AnalyticsAdoptionRateList.as_view(), name='analytics_adoption_rate'),
    re_path(r'^adoption_rate_options/$', analytics.AnalyticsAdoptionRateList.as_view(), name='analytics_adoption_rate_options'),
    re_path(r'^event_explorer/$', analytics.AnalyticsEventExplorerList.as_view(), name='analytics_event_explorer'),
    re_path(r'^event_explorer_options/$', analytics.AnalyticsEventExplorerList.as_view(), name='analytics_event_explorer_options'),
    re_path(r'^host_explorer/$', analytics.AnalyticsHostExplorerList.as_view(), name='analytics_host_explorer'),
    re_path(r'^host_explorer_options/$', analytics.AnalyticsHostExplorerList.as_view(), name='analytics_host_explorer_options'),
    re_path(r'^job_explorer/$', analytics.AnalyticsJobExplorerList.as_view(), name='analytics_job_explorer'),
    re_path(r'^job_explorer_options/$', analytics.AnalyticsJobExplorerList.as_view(), name='analytics_job_explorer_options'),
    re_path(r'^probe_templates/$', analytics.AnalyticsProbeTemplatesList.as_view(), name='analytics_probe_templates_explorer'),
    re_path(r'^probe_templates_options/$', analytics.AnalyticsProbeTemplatesList.as_view(), name='analytics_probe_templates_options'),
    re_path(r'^probe_template_for_hosts/$', analytics.AnalyticsProbeTemplateForHostsList.as_view(), name='analytics_probe_template_for_hosts_explorer'),
    re_path(r'^probe_template_for_hosts_options/$', analytics.AnalyticsProbeTemplateForHostsList.as_view(), name='analytics_probe_template_for_hosts_options'),
    re_path(r'^roi_templates/$', analytics.AnalyticsRoiTemplatesList.as_view(), name='analytics_roi_templates_explorer'),
    re_path(r'^roi_templates_options/$', analytics.AnalyticsRoiTemplatesList.as_view(), name='analytics_roi_templates_options'),
]

__all__ = ['urls']
