# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

from django.conf.urls import include, patterns, url as original_url 
import ansibleworks.main.views as views

def url(regex, view, kwargs=None, name=None, prefix=''):
    # Set default name from view name (if a string).
    if isinstance(view, basestring) and name is None:
        name = view
    return original_url(regex, view, kwargs, name, prefix)

organizations_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'organizations_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'organizations_detail'),
    url(r'^(?P<pk>[0-9]+)/audit_trail/$',               'organizations_audit_trail_list'),
    url(r'^(?P<pk>[0-9]+)/users/$',                     'organizations_users_list'),
    url(r'^(?P<pk>[0-9]+)/admins/$',                    'organizations_admins_list'),
    url(r'^(?P<pk>[0-9]+)/inventories/$',               'organizations_inventories_list'),
    url(r'^(?P<pk>[0-9]+)/projects/$',                  'organizations_projects_list'),
    url(r'^(?P<pk>[0-9]+)/tags/$',                      'organizations_tags_list'),
    url(r'^(?P<pk>[0-9]+)/teams/$',                     'organizations_teams_list'),
)

users_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'users_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'users_detail'),
    url(r'^(?P<pk>[0-9]+)/teams/$',                     'users_teams_list'),
    url(r'^(?P<pk>[0-9]+)/organizations/$',             'users_organizations_list'),
    url(r'^(?P<pk>[0-9]+)/admin_of_organizations/$',    'users_admin_organizations_list'),
    url(r'^(?P<pk>[0-9]+)/projects/$',                  'users_projects_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$',               'users_credentials_list'),
    url(r'^(?P<pk>[0-9]+)/permissions/$',               'users_permissions_list'),
)

projects_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'projects_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'projects_detail'),
    url(r'^(?P<pk>[0-9]+)/playbooks/$',                 'projects_detail_playbooks'),
    url(r'^(?P<pk>[0-9]+)/organizations/$',             'projects_organizations_list'),
)

audit_trails_urls = patterns('ansibleworks.main.views',
    #url(r'^$',                                          'audit_trails_list'),
    #url(r'^(?P<pk>[0-9]+)/$',                           'audit_trails_detail'),
    # ... and ./audit_trails/ on all resources
)

teams_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'teams_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'teams_detail'),
    url(r'^(?P<pk>[0-9]+)/projects/$',                  'teams_projects_list'),
    url(r'^(?P<pk>[0-9]+)/users/$',                     'teams_users_list'),
    url(r'^(?P<pk>[0-9]+)/credentials/$',               'teams_credentials_list'),
    url(r'^(?P<pk>[0-9]+)/permissions/$',               'teams_permissions_list'),
)

inventory_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'inventory_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'inventory_detail'),
    url(r'^(?P<pk>[0-9]+)/hosts/$',                     'inventory_hosts_list'),
    url(r'^(?P<pk>[0-9]+)/groups/$',                    'inventory_groups_list'),
    url(r'^(?P<pk>[0-9]+)/root_groups/$',               'inventory_root_groups_list'),
)

hosts_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'hosts_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'hosts_detail'),
    url(r'^(?P<pk>[0-9]+)/variable_data/$',             'hosts_variable_detail'),
    url(r'^(?P<pk>[0-9]+)/job_events/',                 'host_job_event_list'),
    url(r'^(?P<pk>[0-9]+)/job_host_summaries/$',        'host_job_host_summary_list'),
)

groups_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'groups_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'groups_detail'),
    url(r'^(?P<pk>[0-9]+)/children/$',                  'groups_children_list'),
    url(r'^(?P<pk>[0-9]+)/hosts/$',                     'groups_hosts_list'),
    url(r'^(?P<pk>[0-9]+)/all_hosts/$',                 'groups_all_hosts_list'),
    url(r'^(?P<pk>[0-9]+)/variable_data/$',             'groups_variable_detail'),
    url(r'^(?P<pk>[0-9]+)/job_events/$',                'group_job_event_list'),
    url(r'^(?P<pk>[0-9]+)/job_host_summaries/$',        'group_job_host_summary_list'),
)

variable_data_urls = patterns('ansibleworks.main.views',
    url(r'^(?P<pk>[0-9]+)/$',                           'variable_detail'),
    # See also variable_data resources on hosts/groups.
)

credentials_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'credentials_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'credentials_detail'),
    # See also credentials resources on users/teams.
)

permissions_urls = patterns('ansibleworks.main.views',
    url(r'^(?P<pk>[0-9]+)/$',                           'permissions_detail'),
)

job_templates_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'job_template_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'job_template_detail'),
    url(r'^(?P<pk>[0-9]+)/jobs/$',                      'job_template_job_list'),
)

jobs_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'job_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'job_detail'),
    url(r'^(?P<pk>[0-9]+)/start/$',                     'job_start'),
    url(r'^(?P<pk>[0-9]+)/cancel/$',                    'job_cancel'),
    url(r'^(?P<pk>[0-9]+)/job_host_summaries/$',        'job_job_host_summary_list'),
    #url(r'^(?P<pk>[0-9]+)/successful_hosts/$',          'jobs_successful_hosts_list'),
    #url(r'^(?P<pk>[0-9]+)/changed_hosts/$',             'jobs_changed_hosts_list'),
    #url(r'^(?P<pk>[0-9]+)/failed_hosts/$',              'jobs_failed_hosts_list'),
    #url(r'^(?P<pk>[0-9]+)/unreachable_hosts/$',         'jobs_unreachable_hosts_list'),
    url(r'^(?P<pk>[0-9]+)/job_events/$',                'job_job_event_list'),
)

job_host_summary_urls = patterns('ansibleworks.main.views',
    url(r'^(?P<pk>[0-9]+)/$',                           'job_host_summary_detail'),
)

job_events_urls = patterns('ansibleworks.main.views',
    url(r'^$',                                          'job_event_list'),
    url(r'^(?P<pk>[0-9]+)/$',                           'job_event_detail'),
)

tags_urls = patterns('ansibleworks.main.views',
    url(r'^(?P<pk>[0-9]+)/$',                           'tags_detail'),
    # ... and tag relations on all resources
)

v1_urls = patterns('ansibleworks.main.views',
    url(r'^$',              'api_v1_root_view'),
    url(r'^authtoken/$',    'auth_token_view'),
    url(r'^me/$',           'users_me_list'),
    url(r'^organizations/', include(organizations_urls)),
    url(r'^users/',         include(users_urls)),
    url(r'^projects/',      include(projects_urls)),
    url(r'^audit_trails/',  include(audit_trails_urls)),
    url(r'^teams/',         include(teams_urls)),
    url(r'^inventories/',   include(inventory_urls)),
    url(r'^hosts/',         include(hosts_urls)),
    url(r'^groups/',        include(groups_urls)),
    url(r'^variable_data/', include(variable_data_urls)),
    url(r'^credentials/',   include(credentials_urls)),
    url(r'^permissions/',   include(permissions_urls)),
    url(r'^job_templates/', include(job_templates_urls)),
    url(r'^jobs/',          include(jobs_urls)),
    url(r'^job_host_summaries/', include(job_host_summary_urls)),
    url(r'^job_events/',    include(job_events_urls)),
    url(r'^tags/',          include(tags_urls)),
)

urlpatterns = patterns('ansibleworks.main.views',
    url(r'^$', 'api_root_view'),
    url(r'^v1/', include(v1_urls)),
)
