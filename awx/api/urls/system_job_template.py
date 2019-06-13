# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import url

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
    url(r'^$', SystemJobTemplateList.as_view(), name='system_job_template_list'),
    url(r'^(?P<pk>[0-9]+)/$', SystemJobTemplateDetail.as_view(), name='system_job_template_detail'),
    url(r'^(?P<pk>[0-9]+)/launch/$', SystemJobTemplateLaunch.as_view(), name='system_job_template_launch'),
    url(r'^(?P<pk>[0-9]+)/jobs/$', SystemJobTemplateJobsList.as_view(), name='system_job_template_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/schedules/$', SystemJobTemplateSchedulesList.as_view(), name='system_job_template_schedules_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_started/$', SystemJobTemplateNotificationTemplatesStartedList.as_view(),
        name='system_job_template_notification_templates_started_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$', SystemJobTemplateNotificationTemplatesErrorList.as_view(),
        name='system_job_template_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$', SystemJobTemplateNotificationTemplatesSuccessList.as_view(),
        name='system_job_template_notification_templates_success_list'),
]

__all__ = ['urls']
