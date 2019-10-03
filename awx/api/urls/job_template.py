# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.conf.urls import include, url

from awx.api.views import (
    JobTemplateList,
    JobTemplateDetail,
    JobTemplateLaunch,
    JobTemplateJobsList,
    JobTemplateSliceWorkflowJobsList,
    JobTemplateCallback,
    JobTemplateSchedulesList,
    JobTemplateSurveySpec,
    JobTemplateActivityStreamList,
    JobTemplateNotificationTemplatesErrorList,
    JobTemplateNotificationTemplatesStartedList,
    JobTemplateNotificationTemplatesSuccessList,
    JobTemplateInstanceGroupsList,
    JobTemplateAccessList,
    JobTemplateObjectRolesList,
    JobTemplateLabelList,
    JobTemplateCopy,
)


urls = [
    url(r'^$', JobTemplateList.as_view(), name='job_template_list'),
    url(r'^(?P<pk>[0-9]+)/$', JobTemplateDetail.as_view(), name='job_template_detail'),
    url(r'^(?P<pk>[0-9]+)/launch/$', JobTemplateLaunch.as_view(), name='job_template_launch'),
    url(r'^(?P<pk>[0-9]+)/jobs/$', JobTemplateJobsList.as_view(), name='job_template_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/slice_workflow_jobs/$', JobTemplateSliceWorkflowJobsList.as_view(), name='job_template_slice_workflow_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/callback/$', JobTemplateCallback.as_view(), name='job_template_callback'),
    url(r'^(?P<pk>[0-9]+)/schedules/$', JobTemplateSchedulesList.as_view(), name='job_template_schedules_list'),
    url(r'^(?P<pk>[0-9]+)/survey_spec/$', JobTemplateSurveySpec.as_view(), name='job_template_survey_spec'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$', JobTemplateActivityStreamList.as_view(), name='job_template_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_started/$', JobTemplateNotificationTemplatesStartedList.as_view(),
        name='job_template_notification_templates_started_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$', JobTemplateNotificationTemplatesErrorList.as_view(),
        name='job_template_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$', JobTemplateNotificationTemplatesSuccessList.as_view(),
        name='job_template_notification_templates_success_list'),
    url(r'^(?P<pk>[0-9]+)/instance_groups/$', JobTemplateInstanceGroupsList.as_view(), name='job_template_instance_groups_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$', JobTemplateAccessList.as_view(), name='job_template_access_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$', JobTemplateObjectRolesList.as_view(), name='job_template_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/labels/$', JobTemplateLabelList.as_view(), name='job_template_label_list'),
    url(r'^(?P<pk>[0-9]+)/copy/$', JobTemplateCopy.as_view(), name='job_template_copy'),
    url(r'^(?P<pk>[0-9]+)/', include('awx.api.urls.webhooks'), {'model_kwarg': 'job_templates'}),
]

__all__ = ['urls']
