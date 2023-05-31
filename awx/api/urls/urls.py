# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from __future__ import absolute_import, unicode_literals
from django.urls import include, re_path

from awx import MODE
from awx.api.generics import LoggedLoginView, LoggedLogoutView
from awx.api.views.root import (
    ApiRootView,
    ApiV2RootView,
    ApiV2PingView,
    ApiV2ConfigView,
    ApiV2SubscriptionView,
    ApiV2AttachView,
)
from awx.api.views import (
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
    # HostMetricSummaryMonthlyList, # It will be enabled in future version of the AWX
)

from awx.api.views.bulk import (
    BulkView,
    BulkHostCreateView,
    BulkJobLaunchView,
)

from awx.api.views.mesh_visualizer import MeshVisualizer

from awx.api.views.metrics import MetricsView
from awx.api.views.analytics import AWX_ANALYTICS_API_PREFIX

from .organization import urls as organization_urls
from .user import urls as user_urls
from .project import urls as project_urls
from .project_update import urls as project_update_urls
from .inventory import urls as inventory_urls, constructed_inventory_urls
from .execution_environments import urls as execution_environment_urls
from .team import urls as team_urls
from .host import urls as host_urls
from .host_metric import urls as host_metric_urls
from .group import urls as group_urls
from .inventory_source import urls as inventory_source_urls
from .inventory_update import urls as inventory_update_urls
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
from .analytics import urls as analytics_urls

v2_urls = [
    re_path(r'^$', ApiV2RootView.as_view(), name='api_v2_root_view'),
    re_path(r'^credential_types/', include(credential_type_urls)),
    re_path(r'^credential_input_sources/', include(credential_input_source_urls)),
    re_path(r'^hosts/(?P<pk>[0-9]+)/ansible_facts/$', HostAnsibleFactsDetail.as_view(), name='host_ansible_facts_detail'),
    re_path(r'^jobs/(?P<pk>[0-9]+)/credentials/$', JobCredentialsList.as_view(), name='job_credentials_list'),
    re_path(r'^job_templates/(?P<pk>[0-9]+)/credentials/$', JobTemplateCredentialsList.as_view(), name='job_template_credentials_list'),
    re_path(r'^schedules/preview/$', SchedulePreview.as_view(), name='schedule_rrule'),
    re_path(r'^schedules/zoneinfo/$', ScheduleZoneInfo.as_view(), name='schedule_zoneinfo'),
    re_path(r'^applications/$', OAuth2ApplicationList.as_view(), name='o_auth2_application_list'),
    re_path(r'^applications/(?P<pk>[0-9]+)/$', OAuth2ApplicationDetail.as_view(), name='o_auth2_application_detail'),
    re_path(r'^applications/(?P<pk>[0-9]+)/tokens/$', ApplicationOAuth2TokenList.as_view(), name='application_o_auth2_token_list'),
    re_path(r'^tokens/$', OAuth2TokenList.as_view(), name='o_auth2_token_list'),
    re_path(r'^', include(oauth2_urls)),
    re_path(r'^metrics/$', MetricsView.as_view(), name='metrics_view'),
    re_path(r'^ping/$', ApiV2PingView.as_view(), name='api_v2_ping_view'),
    re_path(r'^config/$', ApiV2ConfigView.as_view(), name='api_v2_config_view'),
    re_path(r'^config/subscriptions/$', ApiV2SubscriptionView.as_view(), name='api_v2_subscription_view'),
    re_path(r'^config/attach/$', ApiV2AttachView.as_view(), name='api_v2_attach_view'),
    re_path(r'^auth/$', AuthView.as_view()),
    re_path(r'^me/$', UserMeList.as_view(), name='user_me_list'),
    re_path(r'^dashboard/$', DashboardView.as_view(), name='dashboard_view'),
    re_path(r'^dashboard/graphs/jobs/$', DashboardJobsGraphView.as_view(), name='dashboard_jobs_graph_view'),
    re_path(r'^mesh_visualizer/', MeshVisualizer.as_view(), name='mesh_visualizer_view'),
    re_path(r'^settings/', include('awx.conf.urls')),
    re_path(r'^instances/', include(instance_urls)),
    re_path(r'^instance_groups/', include(instance_group_urls)),
    re_path(r'^schedules/', include(schedule_urls)),
    re_path(r'^organizations/', include(organization_urls)),
    re_path(r'^users/', include(user_urls)),
    re_path(r'^execution_environments/', include(execution_environment_urls)),
    re_path(r'^projects/', include(project_urls)),
    re_path(r'^project_updates/', include(project_update_urls)),
    re_path(r'^teams/', include(team_urls)),
    re_path(r'^inventories/', include(inventory_urls)),
    re_path(r'^constructed_inventories/', include(constructed_inventory_urls)),
    re_path(r'^hosts/', include(host_urls)),
    re_path(r'^host_metrics/', include(host_metric_urls)),
    # It will be enabled in future version of the AWX
    # re_path(r'^host_metric_summary_monthly/$', HostMetricSummaryMonthlyList.as_view(), name='host_metric_summary_monthly_list'),
    re_path(r'^groups/', include(group_urls)),
    re_path(r'^inventory_sources/', include(inventory_source_urls)),
    re_path(r'^inventory_updates/', include(inventory_update_urls)),
    re_path(r'^credentials/', include(credential_urls)),
    re_path(r'^roles/', include(role_urls)),
    re_path(r'^job_templates/', include(job_template_urls)),
    re_path(r'^jobs/', include(job_urls)),
    re_path(r'^job_host_summaries/', include(job_host_summary_urls)),
    re_path(r'^job_events/', include(job_event_urls)),
    re_path(r'^ad_hoc_commands/', include(ad_hoc_command_urls)),
    re_path(r'^ad_hoc_command_events/', include(ad_hoc_command_event_urls)),
    re_path(r'^system_job_templates/', include(system_job_template_urls)),
    re_path(r'^system_jobs/', include(system_job_urls)),
    re_path(r'^notification_templates/', include(notification_template_urls)),
    re_path(r'^notifications/', include(notification_urls)),
    re_path(r'^workflow_job_templates/', include(workflow_job_template_urls)),
    re_path(r'^workflow_jobs/', include(workflow_job_urls)),
    re_path(r'^labels/', include(label_urls)),
    re_path(r'^workflow_job_template_nodes/', include(workflow_job_template_node_urls)),
    re_path(r'^workflow_job_nodes/', include(workflow_job_node_urls)),
    re_path(r'^unified_job_templates/$', UnifiedJobTemplateList.as_view(), name='unified_job_template_list'),
    re_path(r'^unified_jobs/$', UnifiedJobList.as_view(), name='unified_job_list'),
    re_path(r'^activity_stream/', include(activity_stream_urls)),
    re_path(rf'^{AWX_ANALYTICS_API_PREFIX}/', include(analytics_urls)),
    re_path(r'^workflow_approval_templates/', include(workflow_approval_template_urls)),
    re_path(r'^workflow_approvals/', include(workflow_approval_urls)),
    re_path(r'^bulk/$', BulkView.as_view(), name='bulk'),
    re_path(r'^bulk/host_create/$', BulkHostCreateView.as_view(), name='bulk_host_create'),
    re_path(r'^bulk/job_launch/$', BulkJobLaunchView.as_view(), name='bulk_job_launch'),
]


app_name = 'api'
urlpatterns = [
    re_path(r'^$', ApiRootView.as_view(), name='api_root_view'),
    re_path(r'^(?P<version>(v2))/', include(v2_urls)),
    re_path(r'^login/$', LoggedLoginView.as_view(template_name='rest_framework/login.html', extra_context={'inside_login_context': True}), name='login'),
    re_path(r'^logout/$', LoggedLogoutView.as_view(next_page='/api/', redirect_field_name='next'), name='logout'),
    re_path(r'^o/', include(oauth2_root_urls)),
]
if MODE == 'development':
    # Only include these if we are in the development environment
    from awx.api.swagger import schema_view

    from awx.api.urls.debug import urls as debug_urls

    urlpatterns += [re_path(r'^debug/', include(debug_urls))]
    urlpatterns += [
        re_path(r'^swagger(?P<format>\.json|\.yaml)/$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]
