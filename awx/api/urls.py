# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# noqa

from django.conf.urls import include, patterns, url as original_url

def url(regex, view, kwargs=None, name=None, prefix=''):
    # Set default name from view name (if a string).
    if isinstance(view, basestring) and name is None:
        name = view
    return original_url(regex, view, kwargs, name, prefix)

organization_urls = patterns('awx.api.views',
    url(r'^$',                                          'organization_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'organization_detail'),
    url(r'^(?P<pk>[0-9]+)/users/$',                     'organization_users_list'),
    url(r'^(?P<pk>[0-9]+)/admins/$',                    'organization_admins_list'),
    url(r'^(?P<pk>[0-9]+)/inventories/$',               'organization_inventories_list'),
    url(r'^(?P<pk>[0-9]+)/projects/$',                  'organization_projects_list'),
    url(r'^(?P<pk>[0-9]+)/workflow_job_templates/$',    'organization_workflow_job_templates_list'),
    url(r'^(?P<pk>[0-9]+)/teams/$',                     'organization_teams_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$',               'organization_credential_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'organization_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates/$',                 'organization_notification_templates_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_any/$',             'organization_notification_templates_any_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$',           'organization_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$',         'organization_notification_templates_success_list'),
    url(r'^(?P<pk>[0-9]+)/instance_groups/$',                        'organization_instance_groups_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$',              'organization_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$',               'organization_access_list'),
)

user_urls = patterns('awx.api.views',
    url(r'^$',                                          'user_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'user_detail'),
    url(r'^(?P<pk>[0-9]+)/teams/$',                     'user_teams_list'),
    url(r'^(?P<pk>[0-9]+)/organizations/$',             'user_organizations_list'),
    url(r'^(?P<pk>[0-9]+)/admin_of_organizations/$',    'user_admin_of_organizations_list'),
    url(r'^(?P<pk>[0-9]+)/projects/$',                  'user_projects_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$',               'user_credentials_list'),
    url(r'^(?P<pk>[0-9]+)/roles/$',                     'user_roles_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'user_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$',               'user_access_list'),

)

project_urls = patterns('awx.api.views',
    url(r'^$',                                          'project_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'project_detail'),
    url(r'^(?P<pk>[0-9]+)/playbooks/$',                 'project_playbooks'),
    url(r'^(?P<pk>[0-9]+)/inventories/$',               'project_inventories'),
    url(r'^(?P<pk>[0-9]+)/scm_inventory_sources/$',     'project_scm_inventory_sources'),
    url(r'^(?P<pk>[0-9]+)/teams/$',                     'project_teams_list'),
    url(r'^(?P<pk>[0-9]+)/update/$',                    'project_update_view'),
    url(r'^(?P<pk>[0-9]+)/project_updates/$',           'project_updates_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'project_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/schedules/$',                 'project_schedules_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_any/$',             'project_notification_templates_any_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$',           'project_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$',         'project_notification_templates_success_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$',              'project_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$',               'project_access_list'),
)

project_update_urls = patterns('awx.api.views',
    url(r'^$',                                          'project_update_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'project_update_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$',                    'project_update_cancel'),
    url(r'^(?P<pk>[0-9]+)/stdout/$',                    'project_update_stdout'),
    url(r'^(?P<pk>[0-9]+)/scm_inventory_updates/$',     'project_update_scm_inventory_updates'),
    url(r'^(?P<pk>[0-9]+)/notifications/$',             'project_update_notifications_list'),
)

team_urls = patterns('awx.api.views',
    url(r'^$',                                          'team_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'team_detail'),
    url(r'^(?P<pk>[0-9]+)/projects/$',                  'team_projects_list'),
    url(r'^(?P<pk>[0-9]+)/users/$',                     'team_users_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$',               'team_credentials_list'),
    url(r'^(?P<pk>[0-9]+)/roles/$',                     'team_roles_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$',              'team_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'team_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$',               'team_access_list'),
)

inventory_urls = patterns('awx.api.views',
    url(r'^$',                                          'inventory_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'inventory_detail'),
    url(r'^(?P<pk>[0-9]+)/hosts/$',                     'inventory_hosts_list'),
    url(r'^(?P<pk>[0-9]+)/groups/$',                    'inventory_groups_list'),
    url(r'^(?P<pk>[0-9]+)/root_groups/$',               'inventory_root_groups_list'),
    url(r'^(?P<pk>[0-9]+)/variable_data/$',             'inventory_variable_data'),
    url(r'^(?P<pk>[0-9]+)/script/$',                    'inventory_script_view'),
    url(r'^(?P<pk>[0-9]+)/tree/$',                      'inventory_tree_view'),
    url(r'^(?P<pk>[0-9]+)/inventory_sources/$',         'inventory_inventory_sources_list'),
    url(r'^(?P<pk>[0-9]+)/update_inventory_sources/$',  'inventory_inventory_sources_update'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'inventory_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/job_templates/$',             'inventory_job_template_list'),
    url(r'^(?P<pk>[0-9]+)/ad_hoc_commands/$',           'inventory_ad_hoc_commands_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$',               'inventory_access_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$',              'inventory_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/instance_groups/$',           'inventory_instance_groups_list'),
    #url(r'^(?P<pk>[0-9]+)/single_fact/$',                'inventory_single_fact_view'),
)

host_urls = patterns('awx.api.views',
    url(r'^$',                                          'host_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'host_detail'),
    url(r'^(?P<pk>[0-9]+)/variable_data/$',             'host_variable_data'),
    url(r'^(?P<pk>[0-9]+)/groups/$',                    'host_groups_list'),
    url(r'^(?P<pk>[0-9]+)/all_groups/$',                'host_all_groups_list'),
    url(r'^(?P<pk>[0-9]+)/job_events/',                 'host_job_events_list'),
    url(r'^(?P<pk>[0-9]+)/job_host_summaries/$',        'host_job_host_summaries_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'host_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/inventory_sources/$',         'host_inventory_sources_list'),
    url(r'^(?P<pk>[0-9]+)/smart_inventories/$',         'host_smart_inventories_list'),
    url(r'^(?P<pk>[0-9]+)/ad_hoc_commands/$',           'host_ad_hoc_commands_list'),
    url(r'^(?P<pk>[0-9]+)/ad_hoc_command_events/$',     'host_ad_hoc_command_events_list'),
    #url(r'^(?P<pk>[0-9]+)/single_fact/$',                'host_single_fact_view'),
    url(r'^(?P<pk>[0-9]+)/fact_versions/$',             'host_fact_versions_list'),
    url(r'^(?P<pk>[0-9]+)/fact_view/$',                 'host_fact_compare_view'),
    url(r'^(?P<pk>[0-9]+)/insights/$',                  'host_insights'),
)

group_urls = patterns('awx.api.views',
    url(r'^$',                                          'group_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'group_detail'),
    url(r'^(?P<pk>[0-9]+)/children/$',                  'group_children_list'),
    url(r'^(?P<pk>[0-9]+)/hosts/$',                     'group_hosts_list'),
    url(r'^(?P<pk>[0-9]+)/all_hosts/$',                 'group_all_hosts_list'),
    url(r'^(?P<pk>[0-9]+)/variable_data/$',             'group_variable_data'),
    url(r'^(?P<pk>[0-9]+)/job_events/$',                'group_job_events_list'),
    url(r'^(?P<pk>[0-9]+)/job_host_summaries/$',        'group_job_host_summaries_list'),
    url(r'^(?P<pk>[0-9]+)/potential_children/$',        'group_potential_children_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'group_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/inventory_sources/$',         'group_inventory_sources_list'),
    url(r'^(?P<pk>[0-9]+)/ad_hoc_commands/$',           'group_ad_hoc_commands_list'),
    #url(r'^(?P<pk>[0-9]+)/single_fact/$',                'group_single_fact_view'),
)

inventory_source_urls = patterns('awx.api.views',
    url(r'^$',                                          'inventory_source_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'inventory_source_detail'),
    url(r'^(?P<pk>[0-9]+)/update/$',                    'inventory_source_update_view'),
    url(r'^(?P<pk>[0-9]+)/inventory_updates/$',         'inventory_source_updates_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'inventory_source_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/schedules/$',                 'inventory_source_schedules_list'),
    url(r'^(?P<pk>[0-9]+)/groups/$',                    'inventory_source_groups_list'),
    url(r'^(?P<pk>[0-9]+)/hosts/$',                     'inventory_source_hosts_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_any/$',             'inventory_source_notification_templates_any_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$',           'inventory_source_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$',         'inventory_source_notification_templates_success_list'),
)

inventory_update_urls = patterns('awx.api.views',
    url(r'^$',                                          'inventory_update_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'inventory_update_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$',                    'inventory_update_cancel'),
    url(r'^(?P<pk>[0-9]+)/stdout/$',                    'inventory_update_stdout'),
    url(r'^(?P<pk>[0-9]+)/notifications/$',             'inventory_update_notifications_list'),
)

inventory_script_urls = patterns('awx.api.views',
    url(r'^$',                                          'inventory_script_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'inventory_script_detail'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$',              'inventory_script_object_roles_list'),
)

credential_type_urls = patterns('awx.api.views',
    url(r'^$',                                          'credential_type_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'credential_type_detail'),
    url(r'^(?P<pk>[0-9]+)/credentials/$',               'credential_type_credential_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'credential_type_activity_stream_list'),
)

credential_urls = patterns('awx.api.views',
    url(r'^$',                                          'credential_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'credential_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'credential_detail'),
    url(r'^(?P<pk>[0-9]+)/access_list/$',               'credential_access_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$',              'credential_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/owner_users/$',               'credential_owner_users_list'),
    url(r'^(?P<pk>[0-9]+)/owner_teams/$',               'credential_owner_teams_list'),
    # See also credentials resources on users/teams.
)

role_urls = patterns('awx.api.views',
    url(r'^$',                                          'role_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'role_detail'),
    url(r'^(?P<pk>[0-9]+)/users/$',                     'role_users_list'),
    url(r'^(?P<pk>[0-9]+)/teams/$',                     'role_teams_list'),
    url(r'^(?P<pk>[0-9]+)/parents/$',                   'role_parents_list'),
    url(r'^(?P<pk>[0-9]+)/children/$',                  'role_children_list'),
)

job_template_urls = patterns('awx.api.views',
    url(r'^$',                                          'job_template_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'job_template_detail'),
    url(r'^(?P<pk>[0-9]+)/launch/$',                    'job_template_launch'),
    url(r'^(?P<pk>[0-9]+)/jobs/$',                      'job_template_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/callback/$',                  'job_template_callback'),
    url(r'^(?P<pk>[0-9]+)/schedules/$',                 'job_template_schedules_list'),
    url(r'^(?P<pk>[0-9]+)/survey_spec/$',               'job_template_survey_spec'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'job_template_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_any/$',             'job_template_notification_templates_any_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$',           'job_template_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$',         'job_template_notification_templates_success_list'),
    url(r'^(?P<pk>[0-9]+)/instance_groups/$',                        'job_template_instance_groups_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$',               'job_template_access_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$',              'job_template_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/labels/$',                    'job_template_label_list'),
)

job_urls = patterns('awx.api.views',
    url(r'^$',                                          'job_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'job_detail'),
    url(r'^(?P<pk>[0-9]+)/start/$',                     'job_start'),  # TODO: remove in 3.3
    url(r'^(?P<pk>[0-9]+)/cancel/$',                    'job_cancel'),
    url(r'^(?P<pk>[0-9]+)/relaunch/$',                  'job_relaunch'),
    url(r'^(?P<pk>[0-9]+)/job_host_summaries/$',        'job_job_host_summaries_list'),
    url(r'^(?P<pk>[0-9]+)/job_events/$',                'job_job_events_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'job_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/stdout/$',                    'job_stdout'),
    url(r'^(?P<pk>[0-9]+)/notifications/$',             'job_notifications_list'),
    url(r'^(?P<pk>[0-9]+)/labels/$',                    'job_label_list'),
)

job_host_summary_urls = patterns('awx.api.views',
    url(r'^(?P<pk>[0-9]+)/$',                           'job_host_summary_detail'),
)

job_event_urls = patterns('awx.api.views',
    url(r'^$',                                          'job_event_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'job_event_detail'),
    url(r'^(?P<pk>[0-9]+)/children/$',                  'job_event_children_list'),
    url(r'^(?P<pk>[0-9]+)/hosts/$',                     'job_event_hosts_list'),
)

ad_hoc_command_urls = patterns('awx.api.views',
    url(r'^$',                                          'ad_hoc_command_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'ad_hoc_command_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$',                    'ad_hoc_command_cancel'),
    url(r'^(?P<pk>[0-9]+)/relaunch/$',                  'ad_hoc_command_relaunch'),
    url(r'^(?P<pk>[0-9]+)/events/$',                    'ad_hoc_command_ad_hoc_command_events_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'ad_hoc_command_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/notifications/$',             'ad_hoc_command_notifications_list'),
    url(r'^(?P<pk>[0-9]+)/stdout/$',                    'ad_hoc_command_stdout'),
)

ad_hoc_command_event_urls = patterns('awx.api.views',
    url(r'^$',                                          'ad_hoc_command_event_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'ad_hoc_command_event_detail'),
)

system_job_template_urls = patterns('awx.api.views',
    url(r'^$',                                          'system_job_template_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'system_job_template_detail'),
    url(r'^(?P<pk>[0-9]+)/launch/$',                    'system_job_template_launch'),
    url(r'^(?P<pk>[0-9]+)/jobs/$',                      'system_job_template_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/schedules/$',                 'system_job_template_schedules_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_any/$',             'system_job_template_notification_templates_any_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$',           'system_job_template_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$',         'system_job_template_notification_templates_success_list'),
)

system_job_urls = patterns('awx.api.views',
    url(r'^$',                                          'system_job_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'system_job_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$',                    'system_job_cancel'),
    url(r'^(?P<pk>[0-9]+)/notifications/$',             'system_job_notifications_list'),
)

workflow_job_template_urls = patterns('awx.api.views',
    url(r'^$',                                          'workflow_job_template_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'workflow_job_template_detail'),
    url(r'^(?P<pk>[0-9]+)/workflow_jobs/$',             'workflow_job_template_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/launch/$',                    'workflow_job_template_launch'),
    url(r'^(?P<pk>[0-9]+)/copy/$',                      'workflow_job_template_copy'),
    url(r'^(?P<pk>[0-9]+)/schedules/$',                 'workflow_job_template_schedules_list'),
    url(r'^(?P<pk>[0-9]+)/survey_spec/$',               'workflow_job_template_survey_spec'),
    url(r'^(?P<pk>[0-9]+)/workflow_nodes/$',            'workflow_job_template_workflow_nodes_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'workflow_job_template_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_any/$',             'workflow_job_template_notification_templates_any_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_error/$',           'workflow_job_template_notification_templates_error_list'),
    url(r'^(?P<pk>[0-9]+)/notification_templates_success/$',         'workflow_job_template_notification_templates_success_list'),
    url(r'^(?P<pk>[0-9]+)/access_list/$',               'workflow_job_template_access_list'),
    url(r'^(?P<pk>[0-9]+)/object_roles/$',              'workflow_job_template_object_roles_list'),
    url(r'^(?P<pk>[0-9]+)/labels/$',                    'workflow_job_template_label_list'),
)

workflow_job_urls = patterns('awx.api.views',
    url(r'^$',                                          'workflow_job_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'workflow_job_detail'),
    url(r'^(?P<pk>[0-9]+)/workflow_nodes/$',            'workflow_job_workflow_nodes_list'),
    url(r'^(?P<pk>[0-9]+)/labels/$',                    'workflow_job_label_list'),
    url(r'^(?P<pk>[0-9]+)/cancel/$',                    'workflow_job_cancel'),
    url(r'^(?P<pk>[0-9]+)/relaunch/$',                  'workflow_job_relaunch'),
    url(r'^(?P<pk>[0-9]+)/notifications/$',             'workflow_job_notifications_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'workflow_job_activity_stream_list'),
)


notification_template_urls = patterns('awx.api.views',
    url(r'^$',                                          'notification_template_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'notification_template_detail'),
    url(r'^(?P<pk>[0-9]+)/test/$',                      'notification_template_test'),
    url(r'^(?P<pk>[0-9]+)/notifications/$',             'notification_template_notification_list'),
)

notification_urls = patterns('awx.api.views',
    url(r'^$',                                          'notification_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'notification_detail'),
)

label_urls = patterns('awx.api.views',
    url(r'^$',                                          'label_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'label_detail'),
)

workflow_job_template_node_urls = patterns('awx.api.views',
    url(r'^$',                                          'workflow_job_template_node_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'workflow_job_template_node_detail'),
    url(r'^(?P<pk>[0-9]+)/success_nodes/$',             'workflow_job_template_node_success_nodes_list'),
    url(r'^(?P<pk>[0-9]+)/failure_nodes/$',             'workflow_job_template_node_failure_nodes_list'),
    url(r'^(?P<pk>[0-9]+)/always_nodes/$',              'workflow_job_template_node_always_nodes_list'),
)

workflow_job_node_urls = patterns('awx.api.views',
    url(r'^$',                                          'workflow_job_node_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'workflow_job_node_detail'),
    url(r'^(?P<pk>[0-9]+)/success_nodes/$',             'workflow_job_node_success_nodes_list'),
    url(r'^(?P<pk>[0-9]+)/failure_nodes/$',             'workflow_job_node_failure_nodes_list'),
    url(r'^(?P<pk>[0-9]+)/always_nodes/$',              'workflow_job_node_always_nodes_list'),
)

schedule_urls = patterns('awx.api.views',
    url(r'^$',                                          'schedule_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'schedule_detail'),
    url(r'^(?P<pk>[0-9]+)/jobs/$',                      'schedule_unified_jobs_list'),
)

activity_stream_urls = patterns('awx.api.views',
    url(r'^$',                                          'activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'activity_stream_detail'),
)

instance_urls = patterns('awx.api.views',
    url(r'^$',                                          'instance_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'instance_detail'),
    url(r'^(?P<pk>[0-9]+)/jobs/$',                      'instance_unified_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/instance_groups/$',           'instance_instance_groups_list'),
)

instance_group_urls = patterns('awx.api.views',
    url(r'^$',                                          'instance_group_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'instance_group_detail'),
    url(r'^(?P<pk>[0-9]+)/jobs/$',                      'instance_group_unified_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/instances/$',                 'instance_group_instance_list'),
)

v1_urls = patterns('awx.api.views',
    url(r'^$',                      'api_v1_root_view'),
    url(r'^ping/$',                 'api_v1_ping_view'),
    url(r'^config/$',               'api_v1_config_view'),
    url(r'^auth/$',                 'auth_view'),
    url(r'^authtoken/$',            'auth_token_view'),
    url(r'^me/$',                   'user_me_list'),
    url(r'^dashboard/$',            'dashboard_view'),
    url(r'^dashboard/graphs/jobs/$','dashboard_jobs_graph_view'),
    url(r'^settings/',              include('awx.conf.urls')),
    url(r'^instances/',             include(instance_urls)),
    url(r'^instance_groups/',       include(instance_group_urls)),
    url(r'^schedules/',             include(schedule_urls)),
    url(r'^organizations/',         include(organization_urls)),
    url(r'^users/',                 include(user_urls)),
    url(r'^projects/',              include(project_urls)),
    url(r'^project_updates/',       include(project_update_urls)),
    url(r'^teams/',                 include(team_urls)),
    url(r'^inventories/',           include(inventory_urls)),
    url(r'^hosts/',                 include(host_urls)),
    url(r'^groups/',                include(group_urls)),
    url(r'^inventory_sources/',     include(inventory_source_urls)),
    url(r'^inventory_updates/',     include(inventory_update_urls)),
    url(r'^inventory_scripts/',     include(inventory_script_urls)),
    url(r'^credentials/',           include(credential_urls)),
    url(r'^roles/',                 include(role_urls)),
    url(r'^job_templates/',         include(job_template_urls)),
    url(r'^jobs/',                  include(job_urls)),
    url(r'^job_host_summaries/',    include(job_host_summary_urls)),
    url(r'^job_events/',            include(job_event_urls)),
    url(r'^ad_hoc_commands/',       include(ad_hoc_command_urls)),
    url(r'^ad_hoc_command_events/', include(ad_hoc_command_event_urls)),
    url(r'^system_job_templates/',  include(system_job_template_urls)),
    url(r'^system_jobs/',           include(system_job_urls)),
    url(r'^notification_templates/',             include(notification_template_urls)),
    url(r'^notifications/',         include(notification_urls)),
    url(r'^workflow_job_templates/',include(workflow_job_template_urls)),
    url(r'^workflow_jobs/'          ,include(workflow_job_urls)),
    url(r'^labels/',                include(label_urls)),
    url(r'^workflow_job_template_nodes/',        include(workflow_job_template_node_urls)),
    url(r'^workflow_job_nodes/',    include(workflow_job_node_urls)),
    url(r'^unified_job_templates/$','unified_job_template_list'),
    url(r'^unified_jobs/$',         'unified_job_list'),
    url(r'^activity_stream/',       include(activity_stream_urls)),
)

v2_urls = patterns('awx.api.views',
    url(r'^$',                      'api_v2_root_view'),
    url(r'^credential_types/',     include(credential_type_urls)),
    url(r'^hosts/(?P<pk>[0-9]+)/ansible_facts/$',             'host_ansible_facts_detail'),
    url(r'^jobs/(?P<pk>[0-9]+)/extra_credentials/$',          'job_extra_credentials_list'),
    url(r'^job_templates/(?P<pk>[0-9]+)/extra_credentials/$', 'job_template_extra_credentials_list'),
)

urlpatterns = patterns('awx.api.views',
    url(r'^$', 'api_root_view'),
    url(r'^(?P<version>(v2))/', include(v2_urls)),
    url(r'^(?P<version>(v1|v2))/', include(v1_urls))
)
