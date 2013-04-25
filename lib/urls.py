# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.conf.urls import *
import lib.main.views as views

views_ApiRootView                  = views.ApiRootView.as_view()
views_ApiV1RootView                = views.ApiV1RootView.as_view()

# auth token
views_AuthTokenView                = views.AuthTokenView.as_view()

# organizations service
views_OrganizationsList            = views.OrganizationsList.as_view()
views_OrganizationsDetail          = views.OrganizationsDetail.as_view()
views_OrganizationsAuditTrailList  = views.OrganizationsAuditTrailList.as_view()
views_OrganizationsUsersList       = views.OrganizationsUsersList.as_view()
views_OrganizationsAdminsList      = views.OrganizationsAdminsList.as_view()
views_OrganizationsProjectsList    = views.OrganizationsProjectsList.as_view()
views_OrganizationsTagsList        = views.OrganizationsTagsList.as_view()
views_OrganizationsTeamsList       = views.OrganizationsTeamsList.as_view()

# users service
views_UsersList                    = views.UsersList.as_view()
views_UsersDetail                  = views.UsersDetail.as_view()
views_UsersMeList                  = views.UsersMeList.as_view()
views_UsersTeamsList               = views.UsersTeamsList.as_view()
views_UsersOrganizationsList       = views.UsersOrganizationsList.as_view()
views_UsersAdminOrganizationsList  = views.UsersAdminOrganizationsList.as_view()
views_UsersProjectsList            = views.UsersProjectsList.as_view()
views_UsersCredentialsList         = views.UsersCredentialsList.as_view()

# projects service
views_ProjectsList                 = views.ProjectsList.as_view()
views_ProjectsDetail               = views.ProjectsDetail.as_view()
views_ProjectsOrganizationsList    = views.ProjectsOrganizationsList.as_view()

# audit trail service

# team service
views_TeamsList                    = views.TeamsList.as_view()
views_TeamsDetail                  = views.TeamsDetail.as_view()
views_TeamsUsersList               = views.TeamsUsersList.as_view()
views_TeamsCredentialsList         = views.TeamsCredentialsList.as_view()
views_TeamsCredentialsList         = views.TeamsCredentialsList.as_view()
views_TeamsProjectsList            = views.TeamsProjectsList.as_view()

# inventory service
views_InventoryList                = views.InventoryList.as_view()
views_InventoryDetail              = views.InventoryDetail.as_view()
views_InventoryHostsList           = views.InventoryHostsList.as_view()
views_InventoryGroupsList          = views.InventoryGroupsList.as_view()

# group service
views_GroupsList                   = views.GroupsList.as_view()
views_GroupsDetail                 = views.GroupsDetail.as_view()
views_GroupsVariableDetail         = views.GroupsVariableDetail.as_view()
views_GroupsChildrenList           = views.GroupsChildrenList.as_view()
views_GroupsAllHostsList           = views.GroupsAllHostsList.as_view()
views_GroupsHostsList              = views.GroupsHostsList.as_view()

# host service
views_HostsList                    = views.HostsList.as_view()
views_HostsDetail                  = views.HostsDetail.as_view()
views_HostsVariableDetail          = views.HostsVariableDetail.as_view()

# seperate variable data
views_VariableDetail               = views.VariableDetail.as_view()

# jobs services
views_JobTemplatesList             = views.JobTemplatesList.as_view()
views_JobTemplateDetail            = views.JobTemplateDetail.as_view()
views_JobTemplateStart             = views.JobTemplateStart.as_view()
views_JobsList                     = views.JobsList.as_view()
views_JobsDetail                   = views.JobsDetail.as_view()
views_JobsHostsList                = views.JobsHostsList.as_view()
views_JobsSuccessfulHostsList      = views.JobsSuccessfulHostsList.as_view()
views_JobsChangedHostsList         = views.JobsChangedHostsList.as_view()
views_JobsFailedHostsList          = views.JobsFailedHostsList.as_view()
views_JobsUnreachableHostsList     = views.JobsUnreachableHostsList.as_view()
views_JobsEventsList               = views.JobsEventsList.as_view()
views_JobsEventsDetail             = views.JobsEventsDetail.as_view()
views_HostJobEventsList            = views.HostJobEventsList.as_view()

# tags service
views_TagsDetail                   = views.TagsDetail.as_view()

# credentials service
views_CredentialsDetail            = views.CredentialsDetail.as_view()


urlpatterns = patterns('',

    url(r'^api/$',    views_ApiRootView),
    url(r'^api/v1/$', views_ApiV1RootView),

    # obtain auth token
    url(r'^api/v1/authtoken/$', views_AuthTokenView),

    # organizations vice
    url(r'^api/v1/organizations/$',                               views_OrganizationsList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/$',                views_OrganizationsDetail),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/audit_trail/$',    views_OrganizationsAuditTrailList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/users/$',          views_OrganizationsUsersList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/admins/$',         views_OrganizationsAdminsList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/projects/$',       views_OrganizationsProjectsList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/tags/$',           views_OrganizationsTagsList),
    url(r'^api/v1/organizations/(?P<pk>[0-9]+)/teams/$',          views_OrganizationsTeamsList),

    # users service
    url(r'^api/v1/me/$',                                          views_UsersMeList),
    url(r'^api/v1/users/$',                                       views_UsersList),
    url(r'^api/v1/users/(?P<pk>[0-9]+)/$',                        views_UsersDetail),
    url(r'^api/v1/users/(?P<pk>[0-9]+)/teams/$',                  views_UsersTeamsList),
    url(r'^api/v1/users/(?P<pk>[0-9]+)/organizations/$',          views_UsersOrganizationsList),
    url(r'^api/v1/users/(?P<pk>[0-9]+)/admin_of_organizations/$', views_UsersAdminOrganizationsList),
    url(r'^api/v1/users/(?P<pk>[0-9]+)/projects/$',               views_UsersProjectsList),
    url(r'^api/v1/users/(?P<pk>[0-9]+)/credentials/$',            views_UsersCredentialsList),

    # projects service
    url(r'^api/v1/projects/$',                                    views_ProjectsList),
    url(r'^api/v1/projects/(?P<pk>[0-9]+)/$',                     views_ProjectsDetail),
    url(r'^api/v1/projects/(?P<pk>[0-9]+)/organizations/$',       views_ProjectsOrganizationsList),

    # audit trail service
    # api/v1/audit_trails/
    # api/v1/audit_trails/N/
    # and ./audit_trails/ on all resources

    # team service
    # api/v1/teams/
    url(r'^api/v1/teams/$',                                       views_TeamsList),
    url(r'^api/v1/teams/(?P<pk>[0-9]+)/$',                        views_TeamsDetail),
    url(r'^api/v1/teams/(?P<pk>[0-9]+)/projects/$',               views_TeamsProjectsList),
    url(r'^api/v1/teams/(?P<pk>[0-9]+)/users/$',                  views_TeamsUsersList),
    url(r'^api/v1/teams/(?P<pk>[0-9]+)/credentials/$',            views_TeamsCredentialsList),

    # api/v1/teams/N/
    # api/v1/teams/N/users/

    # inventory service
    url(r'^api/v1/inventories/$',                                 views_InventoryList),
    url(r'^api/v1/inventories/(?P<pk>[0-9]+)/$',                  views_InventoryDetail),
    url(r'^api/v1/inventories/(?P<pk>[0-9]+)/hosts/$',            views_InventoryHostsList),
    url(r'^api/v1/inventories/(?P<pk>[0-9]+)/groups/$',           views_InventoryGroupsList),

    # host service
    url(r'^api/v1/hosts/$',                                       views_HostsList),
    url(r'^api/v1/hosts/(?P<pk>[0-9]+)/$',                        views_HostsDetail),

    # group service
    url(r'^api/v1/groups/$',                                      views_GroupsList),
    url(r'^api/v1/groups/(?P<pk>[0-9]+)/$',                       views_GroupsDetail),
    url(r'^api/v1/groups/(?P<pk>[0-9]+)/children/$',              views_GroupsChildrenList),
    url(r'^api/v1/groups/(?P<pk>[0-9]+)/hosts/$',                 views_GroupsHostsList),
    url(r'^api/v1/groups/(?P<pk>[0-9]+)/all_hosts/$',             views_GroupsAllHostsList),

    # variable data
    url(r'^api/v1/hosts/(?P<pk>[0-9]+)/variable_data/$',          views_HostsVariableDetail),
    url(r'^api/v1/groups/(?P<pk>[0-9]+)/variable_data/$',         views_GroupsVariableDetail),
    url(r'^api/v1/variable_data/(?P<pk>[0-9]+)/$',                views_VariableDetail),

    # log data (results) services

    # jobs & job status services
    url(r'^api/v1/job_templates/$',                               views_JobTemplatesList),
    url(r'^api/v1/job_templates/(?P<pk>[0-9]+)/$',                views_JobTemplateDetail),
    url(r'^api/v1/job_templates/(?P<pk>[0-9]+)/start$',           views_JobTemplateStart),
    url(r'^api/v1/jobs/$',                                        views_JobsList),
    url(r'^api/v1/jobs/(?P<pk>[0-9]+)/$',                         views_JobsDetail),
    url(r'^api/v1/jobs/(?P<pk>[0-9]+)/hosts$',                    views_JobsHostsList),
    url(r'^api/v1/jobs/(?P<pk>[0-9]+)/successful_hosts$',         views_JobsSuccessfulHostsList),
    url(r'^api/v1/jobs/(?P<pk>[0-9]+)/changed_hosts$',            views_JobsChangedHostsList),
    url(r'^api/v1/jobs/(?P<pk>[0-9]+)/failed_hosts$',             views_JobsFailedHostsList),
    url(r'^api/v1/jobs/(?P<pk>[0-9]+)/unreachable_hosts$',        views_JobsUnreachableHostsList),
    url(r'^api/v1/job_events/$',                                  views_JobsEventsList),
    url(r'^api/v1/job_events/(?P<pk>[0-9]+)/$',                   views_JobsEventsDetail),
    url(r'^api/v1/hosts/(?P<pk>[0-9]+)/job_events/',              views_HostJobEventsList),

    # tags service
    url(r'^api/v1/tags/(?P<pk>[0-9]+)/$',                         views_TagsDetail),
    # ... and tag relations on all resources

    # credentials services
    url(r'^api/v1/credentials/(?P<pk>[0-9]+)/$',                  views_CredentialsDetail),

    # permissions services
    # ... users
    # ... teams

)

if 'django.contrib.admin' in settings.INSTALLED_APPS:
    from django.contrib import admin
    admin.autodiscover()
    urlpatterns += patterns('',
        url(r'^admin/', include(admin.site.urls)),
    )
