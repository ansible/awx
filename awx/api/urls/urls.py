# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from __future__ import absolute_import, unicode_literals
from django.conf import settings
from django.conf.urls import include, url

from awx.api.generics import (
    LoggedLoginView,
    LoggedLogoutView,
)
from awx.api.views import (
    ApiRootView,
    ApiV2RootView,
    ApiV2PingView,
    ApiV2ConfigView,
    ApiV2SubscriptionView,
    ApiV2AttachView,
    AuthView,
    UserMeList,
    DashboardView,
    DashboardJobsGraphView,
    UnifiedJobTemplateList,
    UnifiedJobList,
    HostAnsibleFactsDetail,
    JobCredentialsList,
    JobTemplateCredentialsList,
    SchedulePreview,
    ScheduleZoneInfo,
    OAuth2ApplicationList,
    OAuth2TokenList,
    ApplicationOAuth2TokenList,
    OAuth2ApplicationDetail,
)

from awx.api.views.metrics import (
    MetricsView,
)

from .organization import urls as organization_urls
from .user import urls as user_urls
from .project import urls as project_urls
from .project_update import urls as project_update_urls
from .inventory import urls as inventory_urls
from .team import urls as team_urls
from .host import urls as host_urls
from .group import urls as group_urls
from .inventory_source import urls as inventory_source_urls
from .inventory_update import urls as inventory_update_urls
from .inventory_script import urls as inventory_script_urls
from .credential_type import urls as credential_type_urls
from .credential import urls as credential_urls
from .credential_input_source import urls as credential_input_source_urls
from .role import urls as role_urls
from .job_template import urls as job_template_urls
from .job import urls as job_urls
from .job_host_summary import urls as job_host_summary_urls
from .job_event import urls as job_event_urls
from .ad_hoc_command import urls as ad_hoc_command_urls
from .ad_hoc_command_event import urls as ad_hoc_command_event_urls
from .system_job_template import urls as system_job_template_urls
from .system_job import urls as system_job_urls
from .workflow_job_template import urls as workflow_job_template_urls
from .workflow_job import urls as workflow_job_urls
from .notification_template import urls as notification_template_urls
from .notification import urls as notification_urls
from .label import urls as label_urls
from .workflow_job_template_node import urls as workflow_job_template_node_urls
from .workflow_job_node import urls as workflow_job_node_urls
from .schedule import urls as schedule_urls
from .activity_stream import urls as activity_stream_urls
from .instance import urls as instance_urls
from .instance_group import urls as instance_group_urls
from .oauth2 import urls as oauth2_urls
from .oauth2_root import urls as oauth2_root_urls
from .workflow_approval_template import urls as workflow_approval_template_urls
from .workflow_approval import urls as workflow_approval_urls


v2_urls = [
    url(r'^$', ApiV2RootView.as_view(), name='api_v2_root_view'),
    url(r'^credential_types/', include(credential_type_urls)),
    url(r'^credential_input_sources/', include(credential_input_source_urls)),
    url(r'^hosts/(?P<pk>[0-9]+)/ansible_facts/$', HostAnsibleFactsDetail.as_view(), name='host_ansible_facts_detail'),
    url(r'^jobs/(?P<pk>[0-9]+)/credentials/$', JobCredentialsList.as_view(), name='job_credentials_list'),
    url(r'^job_templates/(?P<pk>[0-9]+)/credentials/$', JobTemplateCredentialsList.as_view(), name='job_template_credentials_list'),
    url(r'^schedules/preview/$', SchedulePreview.as_view(), name='schedule_rrule'),
    url(r'^schedules/zoneinfo/$', ScheduleZoneInfo.as_view(), name='schedule_zoneinfo'),
    url(r'^applications/$', OAuth2ApplicationList.as_view(), name='o_auth2_application_list'),
    url(r'^applications/(?P<pk>[0-9]+)/$', OAuth2ApplicationDetail.as_view(), name='o_auth2_application_detail'),
    url(r'^applications/(?P<pk>[0-9]+)/tokens/$', ApplicationOAuth2TokenList.as_view(), name='application_o_auth2_token_list'),
    url(r'^tokens/$', OAuth2TokenList.as_view(), name='o_auth2_token_list'),
    url(r'^', include(oauth2_urls)),
    url(r'^metrics/$', MetricsView.as_view(), name='metrics_view'),
    url(r'^ping/$', ApiV2PingView.as_view(), name='api_v2_ping_view'),
    url(r'^config/$', ApiV2ConfigView.as_view(), name='api_v2_config_view'),
    url(r'^config/subscriptions/$', ApiV2SubscriptionView.as_view(), name='api_v2_subscription_view'),
    url(r'^config/attach/$', ApiV2AttachView.as_view(), name='api_v2_attach_view'),
    url(r'^auth/$', AuthView.as_view()),
    url(r'^me/$', UserMeList.as_view(), name='user_me_list'),
    url(r'^dashboard/$', DashboardView.as_view(), name='dashboard_view'),
    url(r'^dashboard/graphs/jobs/$', DashboardJobsGraphView.as_view(), name='dashboard_jobs_graph_view'),
    url(r'^settings/', include('awx.conf.urls')),
    url(r'^instances/', include(instance_urls)),
    url(r'^instance_groups/', include(instance_group_urls)),
    url(r'^schedules/', include(schedule_urls)),
    url(r'^organizations/', include(organization_urls)),
    url(r'^users/', include(user_urls)),
    url(r'^projects/', include(project_urls)),
    url(r'^project_updates/', include(project_update_urls)),
    url(r'^teams/', include(team_urls)),
    url(r'^inventories/', include(inventory_urls)),
    url(r'^hosts/', include(host_urls)),
    url(r'^groups/', include(group_urls)),
    url(r'^inventory_sources/', include(inventory_source_urls)),
    url(r'^inventory_updates/', include(inventory_update_urls)),
    url(r'^inventory_scripts/', include(inventory_script_urls)),
    url(r'^credentials/', include(credential_urls)),
    url(r'^roles/', include(role_urls)),
    url(r'^job_templates/', include(job_template_urls)),
    url(r'^jobs/', include(job_urls)),
    url(r'^job_host_summaries/', include(job_host_summary_urls)),
    url(r'^job_events/', include(job_event_urls)),
    url(r'^ad_hoc_commands/', include(ad_hoc_command_urls)),
    url(r'^ad_hoc_command_events/', include(ad_hoc_command_event_urls)),
    url(r'^system_job_templates/', include(system_job_template_urls)),
    url(r'^system_jobs/', include(system_job_urls)),
    url(r'^notification_templates/', include(notification_template_urls)),
    url(r'^notifications/', include(notification_urls)),
    url(r'^workflow_job_templates/', include(workflow_job_template_urls)),
    url(r'^workflow_jobs/', include(workflow_job_urls)),
    url(r'^labels/', include(label_urls)),
    url(r'^workflow_job_template_nodes/', include(workflow_job_template_node_urls)),
    url(r'^workflow_job_nodes/', include(workflow_job_node_urls)),
    url(r'^unified_job_templates/$', UnifiedJobTemplateList.as_view(), name='unified_job_template_list'),
    url(r'^unified_jobs/$', UnifiedJobList.as_view(), name='unified_job_list'),
    url(r'^activity_stream/', include(activity_stream_urls)),
    url(r'^workflow_approval_templates/', include(workflow_approval_template_urls)),
    url(r'^workflow_approvals/', include(workflow_approval_urls)),
]


app_name = 'api'
urlpatterns = [
    url(r'^$', ApiRootView.as_view(), name='api_root_view'),
    url(r'^(?P<version>(v2))/', include(v2_urls)),
    url(r'^login/$', LoggedLoginView.as_view(
        template_name='rest_framework/login.html',
        extra_context={'inside_login_context': True}
    ), name='login'),
    url(r'^logout/$', LoggedLogoutView.as_view(
        next_page='/api/', redirect_field_name='next'
    ), name='logout'),
    url(r'^o/', include(oauth2_root_urls)),
]
if settings.SETTINGS_MODULE == 'awx.settings.development':
    from awx.api.swagger import SwaggerSchemaView
    urlpatterns += [
        url(r'^swagger/$', SwaggerSchemaView.as_view(), name='swagger_view'),
    ]
