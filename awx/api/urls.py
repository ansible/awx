# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

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
    url(r'^(?P<pk>[0-9]+)/teams/$',                     'organization_teams_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'organization_activity_stream_list'),
)

user_urls = patterns('awx.api.views',
    url(r'^$',                                          'user_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'user_detail'),
    url(r'^(?P<pk>[0-9]+)/teams/$',                     'user_teams_list'),
    url(r'^(?P<pk>[0-9]+)/organizations/$',             'user_organizations_list'),
    url(r'^(?P<pk>[0-9]+)/admin_of_organizations/$',    'user_admin_of_organizations_list'),
    url(r'^(?P<pk>[0-9]+)/projects/$',                  'user_projects_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$',               'user_credentials_list'),
    url(r'^(?P<pk>[0-9]+)/permissions/$',               'user_permissions_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'user_activity_stream_list'),
)

project_urls = patterns('awx.api.views',
    url(r'^$',                                          'project_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'project_detail'),
    url(r'^(?P<pk>[0-9]+)/playbooks/$',                 'project_playbooks'),
    url(r'^(?P<pk>[0-9]+)/organizations/$',             'project_organizations_list'),
    url(r'^(?P<pk>[0-9]+)/teams/$',                     'project_teams_list'),
    url(r'^(?P<pk>[0-9]+)/update/$',                    'project_update_view'),
    url(r'^(?P<pk>[0-9]+)/project_updates/$',           'project_updates_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'project_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/schedules/$',                 'project_schedules_list'),
)

project_update_urls = patterns('awx.api.views',
    url(r'^(?P<pk>[0-9]+)/$',                           'project_update_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$',                    'project_update_cancel'),
    url(r'^(?P<pk>[0-9]+)/stdout/$',                    'project_update_stdout'),
)

team_urls = patterns('awx.api.views',
    url(r'^$',                                          'team_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'team_detail'),
    url(r'^(?P<pk>[0-9]+)/projects/$',                  'team_projects_list'),
    url(r'^(?P<pk>[0-9]+)/users/$',                     'team_users_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$',               'team_credentials_list'),
    url(r'^(?P<pk>[0-9]+)/permissions/$',               'team_permissions_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'team_activity_stream_list'),
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
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'inventory_activity_stream_list'),
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
)

inventory_update_urls = patterns('awx.api.views',
    url(r'^(?P<pk>[0-9]+)/$',                           'inventory_update_detail'),
    url(r'^(?P<pk>[0-9]+)/cancel/$',                    'inventory_update_cancel'),
    url(r'^(?P<pk>[0-9]+)/stdout/$',                    'inventory_update_stdout'),
)

credential_urls = patterns('awx.api.views',
    url(r'^$',                                          'credential_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'credential_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'credential_detail'),
    # See also credentials resources on users/teams.
)

permission_urls = patterns('awx.api.views',
    url(r'^(?P<pk>[0-9]+)/$',                           'permission_detail'),
)

job_template_urls = patterns('awx.api.views',
    url(r'^$',                                          'job_template_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'job_template_detail'),
    url(r'^(?P<pk>[0-9]+)/jobs/$',                      'job_template_jobs_list'),
    url(r'^(?P<pk>[0-9]+)/callback/$',                  'job_template_callback'),
    url(r'^(?P<pk>[0-9]+)/schedules/$',                 'job_template_schedules_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'job_template_activity_stream_list'),
)

job_urls = patterns('awx.api.views',
    url(r'^$',                                          'job_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'job_detail'),
    url(r'^(?P<pk>[0-9]+)/start/$',                     'job_start'),
    url(r'^(?P<pk>[0-9]+)/cancel/$',                    'job_cancel'),
    url(r'^(?P<pk>[0-9]+)/job_host_summaries/$',        'job_job_host_summaries_list'),
    url(r'^(?P<pk>[0-9]+)/job_events/$',                'job_job_events_list'),
    url(r'^(?P<pk>[0-9]+)/activity_stream/$',           'job_activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/stdout/$',                    'job_stdout'),
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

schedule_urls = patterns('awx.api.views',
    url(r'^$',                                          'schedule_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'schedule_detail'),
    url(r'^(?P<pk>[0-9]+)/jobs/$',                      'schedule_unified_jobs_list'),
)

activity_stream_urls = patterns('awx.api.views',
    url(r'^$',                                          'activity_stream_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'activity_stream_detail'),
)

v1_urls = patterns('awx.api.views',
    url(r'^$',                      'api_v1_root_view'),
    url(r'^config/$',               'api_v1_config_view'),
    url(r'^authtoken/$',            'auth_token_view'),
    url(r'^me/$',                   'user_me_list'),
    url(r'^dashboard/$',            'dashboard_view'),
    url(r'^schedules/',            include(schedule_urls)),
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
    url(r'^credentials/',           include(credential_urls)),
    url(r'^permissions/',           include(permission_urls)),
    url(r'^job_templates/',         include(job_template_urls)),
    url(r'^jobs/',                  include(job_urls)),
    url(r'^job_host_summaries/',    include(job_host_summary_urls)),
    url(r'^job_events/',            include(job_event_urls)),
    url(r'^unified_job_templates/$', 'unified_job_template_list'),
    url(r'^unified_jobs/$',         'unified_job_list'),
    url(r'^activity_stream/',       include(activity_stream_urls)),
)

urlpatterns = patterns('awx.api.views',
    url(r'^$', 'api_root_view'),
    url(r'^v1/', include(v1_urls)),
)
