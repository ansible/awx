# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    SystemJobTemplateList,
    SystemJobTemplateDetail,
    SystemJobTemplateLaunch,
    SystemJobTemplateJobsList,
    SystemJobTemplateSchedulesList,
    SystemJobTemplateNotificationTemplatesErrorList,
    SystemJobTemplateNotificationTemplatesStartedList,
    SystemJobTemplateNotificationTemplatesSuccessList,
)


urls = [
    re_path(r'^$', SystemJobTemplateList.as_view(), name='system_job_template_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', SystemJobTemplateDetail.as_view(), name='system_job_template_detail'),
    re_path(r'^(?P<pk>[0-9]+)/launch/$', SystemJobTemplateLaunch.as_view(), name='system_job_template_launch'),
    re_path(r'^(?P<pk>[0-9]+)/jobs/$', SystemJobTemplateJobsList.as_view(), name='system_job_template_jobs_list'),
    re_path(r'^(?P<pk>[0-9]+)/schedules/$', SystemJobTemplateSchedulesList.as_view(), name='system_job_template_schedules_list'),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_started/$',
        SystemJobTemplateNotificationTemplatesStartedList.as_view(),
        name='system_job_template_notification_templates_started_list',
    ),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_error/$',
        SystemJobTemplateNotificationTemplatesErrorList.as_view(),
        name='system_job_template_notification_templates_error_list',
    ),
    re_path(
        r'^(?P<pk>[0-9]+)/notification_templates_success/$',
        SystemJobTemplateNotificationTemplatesSuccessList.as_view(),
        name='system_job_template_notification_templates_success_list',
    ),
]

__all__ = ['urls']
