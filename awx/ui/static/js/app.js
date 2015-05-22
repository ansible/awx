/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * app.js
 *
 * Declare the Tower app, define routes and perform initialization chores.
 *
 */

var urlPrefix;

if ($basePath) {
    urlPrefix = $basePath;
} else {
    // required to make tests work
    var $basePath = '/static/';
    urlPrefix = $basePath;
}

import 'tower/helpers';
import 'tower/forms';
import 'tower/lists';
import 'tower/widgets';
import 'tower/help';
import 'tower/filters';
import {Home, HomeGroups, HomeHosts} from 'tower/controllers/Home';
import {SocketsController} from 'tower/controllers/Sockets';
import {Authenticate} from 'tower/controllers/Authentication';
import {CredentialsAdd, CredentialsEdit, CredentialsList} from 'tower/controllers/Credentials';
import {JobsListController} from 'tower/controllers/Jobs';
import {PortalController} from 'tower/controllers/Portal';

import dataServices from 'tower/services/_data-services';
import dashboardGraphs from 'tower/directives/_dashboard-graphs';

import routeExtensions from 'tower/shared/route-extensions/main';
import breadcrumbs from 'tower/shared/breadcrumbs/main';

// modules
import browserData from 'tower/browser-data/main';

import {JobDetailController} from 'tower/controllers/JobDetail';
import {JobStdoutController} from 'tower/controllers/JobStdout';
import {JobTemplatesList, JobTemplatesAdd, JobTemplatesEdit} from 'tower/controllers/JobTemplates';
import {LicenseController} from 'tower/controllers/License';
import {ScheduleEditController} from 'tower/controllers/Schedules';
import {ProjectsList, ProjectsAdd, ProjectsEdit} from 'tower/controllers/Projects';
import {OrganizationsList, OrganizationsAdd, OrganizationsEdit} from 'tower/controllers/Organizations';
import {InventoriesList, InventoriesAdd, InventoriesEdit, InventoriesManage} from 'tower/controllers/Inventories';
import {AdhocCtrl} from 'tower/controllers/Adhoc';
import {AdminsList} from 'tower/controllers/Admins';
import {UsersList, UsersAdd, UsersEdit} from 'tower/controllers/Users';
import {TeamsList, TeamsAdd, TeamsEdit} from 'tower/controllers/Teams';
import {PermissionsAdd, PermissionsList, PermissionsEdit} from 'tower/controllers/Permissions';
import 'tower/shared/RestServices';
import 'tower/shared/api-loader';
import 'tower/shared/form-generator';
import 'tower/shared/Modal';
import 'tower/shared/prompt-dialog';
import 'tower/shared/directives';
import 'tower/shared/filters';
import 'tower/shared/InventoryTree';
import 'tower/shared/Timer';
import 'tower/shared/Socket';

import 'tower/job-templates/main';
import 'tower/shared/features/main';

/*#if DEBUG#*/
import {__deferLoadIfEnabled} from 'tower/debug';
__deferLoadIfEnabled();
/*#endif#*/

var tower = angular.module('Tower', [
    'ngRoute',
    'ngSanitize',
    'ngCookies',
    'RestServices',
    dataServices.name,
    dashboardGraphs.name,
    routeExtensions.name,
    browserData.name,
    breadcrumbs.name,
    'AuthService',
    'Utilities',
    'LicenseHelper',
    'OrganizationFormDefinition',
    'UserFormDefinition',
    'FormGenerator',
    'OrganizationListDefinition',
    'jobTemplates',
    'UserListDefinition',
    'UserHelper',
    'PromptDialog',
    'ApiLoader',
    'RelatedSearchHelper',
    'SearchHelper',
    'PaginationHelpers',
    'RefreshHelper',
    'AdminListDefinition',
    'CustomInventoryListDefinition',
    'AWDirectives',
    'AdhocFormDefinition',
    'InventoriesListDefinition',
    'InventoryFormDefinition',
    'InventoryHelper',
    'InventoryGroupsDefinition',
    'InventoryHostsDefinition',
    'HostsHelper',
    'AWFilters',
    'ScanJobsListDefinition',
    'HostFormDefinition',
    'HostListDefinition',
    'GroupFormDefinition',
    'GroupListDefinition',
    'GroupsHelper',
    'TeamsListDefinition',
    'TeamFormDefinition',
    'TeamHelper',
    'CredentialsListDefinition',
    'CredentialFormDefinition',
    'LookUpHelper',
    'JobTemplatesListDefinition',
    'PortalJobTemplatesListDefinition',
    'JobTemplateFormDefinition',
    'JobTemplatesHelper',
    'JobSubmissionHelper',
    'ProjectsListDefinition',
    'ProjectFormDefinition',
    'ProjectStatusDefinition',
    'ProjectsHelper',
    'PermissionFormDefinition',
    'PermissionListDefinition',
    'PermissionsHelper',
    'CompletedJobsDefinition',
    'AllJobsDefinition',
    'JobFormDefinition',
    'JobSummaryDefinition',
    'ParseHelper',
    'ChildrenHelper',
    'ProjectPathHelper',
    'md5Helper',
    'AccessHelper',
    'SelectionHelper',
    'HostGroupsFormDefinition',
    'DashboardCountsWidget',
    'DashboardJobsWidget',
    'PortalJobsWidget',
    'StreamWidget',
    'JobsHelper',
    'InventoryGroupsHelpDefinition',
    'InventoryTree',
    'CredentialsHelper',
    'TimerService',
    'StreamListDefinition',
    'HomeGroupListDefinition',
    'HomeHostListDefinition',
    'ActivityDetailDefinition',
    'VariablesHelper',
    'SchedulesListDefinition',
    'ScheduledJobsDefinition',
    'AngularScheduler',
    'Timezones',
    'SchedulesHelper',
    'JobsListDefinition',
    'LogViewerStatusDefinition',
    'LogViewerHelper',
    'LogViewerOptionsDefinition',
    'EventViewerHelper',
    'HostEventsViewerHelper',
    'SurveyHelper',
    'JobDetailHelper',
    'SocketIO',
    'lrInfiniteScroll',
    'LoadConfigHelper',
    'SocketHelper',
    'AboutAnsibleHelpModal',
    'SurveyQuestionFormDefinition',
    'PortalJobsListDefinition',
    'ConfigureTowerHelper',
    'ConfigureTowerJobsListDefinition',
    'CreateCustomInventoryHelper',
    'CustomInventoryListDefinition',
    'AdhocHelper',
    'features',
    'longDateFilter'
])

    .constant('AngularScheduler.partials', urlPrefix + 'lib/angular-scheduler/lib/')
    .constant('AngularScheduler.useTimezone', true)
    .constant('AngularScheduler.showUTCField', true)
    .constant('$timezones.definitions.location', urlPrefix + 'lib/angular-tz-extensions/tz/data')
    .config(['$routeProvider',
        function ($routeProvider) {
            $routeProvider.

            when('/jobs', {
                name: 'jobs',
                templateUrl: urlPrefix + 'partials/jobs.html',
                controller: JobsListController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/portal', {
                name: 'portal',
                templateUrl: urlPrefix + 'partials/portal.html',
                controller: PortalController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/jobs/:id', {
                name: 'jobDetail',
                templateUrl: urlPrefix + 'partials/job_detail.html',
                controller: JobDetailController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }],
                    jobEventsSocket: ['Socket', '$rootScope', function(Socket, $rootScope) {
                        if (!$rootScope.event_socket) {
                            $rootScope.event_socket = Socket({
                                scope: $rootScope,
                                endpoint: "job_events"
                            });
                            $rootScope.event_socket.init();
                            return true;
                        } else {
                            return true;
                        }
                    }]
                }
            }).

            when('/jobs/:id/stdout', {
                name: 'jobsStdout',
                templateUrl: urlPrefix + 'partials/job_stdout.html',
                controller: JobStdoutController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }],
                    jobEventsSocket: ['Socket', '$rootScope', function(Socket, $rootScope) {
                        if (!$rootScope.event_socket) {
                            $rootScope.event_socket = Socket({
                                scope: $rootScope,
                                endpoint: "job_events"
                            });
                            $rootScope.event_socket.init();
                            return true;
                        } else {
                            return true;
                        }
                    }]
                }
            }).

            when('/ad_hoc_commands/:id', {
                name: 'adHocJobStdout',
                templateUrl: urlPrefix + 'partials/job_stdout_adhoc.html',
                controller: JobStdoutController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }],
                    adhocEventsSocket: ['Socket', '$rootScope', function(Socket, $rootScope) {
                        if (!$rootScope.adhoc_event_socket) {
                            $rootScope.adhoc_event_socket = Socket({
                                scope: $rootScope,
                                endpoint: "ad_hoc_command_events"
                            });
                            $rootScope.adhoc_event_socket.init();
                            return true;
                        } else {
                            return true;
                        }
                    }]
                }
            }).

            when('/job_templates', {
                name: 'jobTemplates',
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/job_templates/add', {
                name: 'jobTemplateAdd',
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/job_templates/:template_id', {
                name: 'jobTemplateEdit',
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/job_templates/:id/schedules', {
                name: 'jobTemplateSchedules',
                templateUrl: urlPrefix + 'partials/schedule_detail.html',
                controller: ScheduleEditController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/projects', {
                name: 'projects',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/projects/add', {
                name: 'projectAdd',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/projects/:id', {
                name: 'projectEdit',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/projects/:id/schedules', {
                name: 'projectSchedules',
                templateUrl: urlPrefix + 'partials/schedule_detail.html',
                controller: ScheduleEditController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/projects/:project_id/organizations', {
                name: 'projectOrganizations',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: OrganizationsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/projects/:project_id/organizations/add', {
                name: 'projectOrganizationAdd',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: OrganizationsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/inventories', {
                name: 'inventories',
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: InventoriesList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/inventories/add', {
                name: 'inventoryAdd',
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: InventoriesAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/inventories/:inventory_id', {
                name: 'inventoryEdit',
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: InventoriesEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/inventories/:inventory_id/job_templates/add', {
                name: 'inventoryJobTemplateAdd',
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/inventories/:inventory_id/job_templates/:template_id', {
                name: 'inventoryJobTemplateEdit',
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/inventories/:inventory_id/manage', {
                name: 'inventoryManage',
                templateUrl: urlPrefix + 'partials/inventory-manage.html',
                controller: InventoriesManage,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/inventories/:inventory_id/adhoc', {
                name: 'inventoryAdhoc',
                templateUrl: urlPrefix + 'partials/adhoc.html',
                controller: AdhocCtrl,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/organizations', {
                name: 'organizations',
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: OrganizationsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/organizations/add', {
                name: 'organizationAdd',
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: OrganizationsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/organizations/:organization_id', {
                name: 'organizationEdit',
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: OrganizationsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/organizations/:organization_id/admins', {
                name: 'organizationAdmins',
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: AdminsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/organizations/:organization_id/users', {
                name: 'organizationUsers',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/organizations/:organization_id/users/add', {
                name: 'organizationUserAdd',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/organizations/:organization_id/users/:user_id', {
                name: 'organizationUserEdit',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams', {
                name: 'teams',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/add', {
                name: 'teamsAdd',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id', {
                name: 'teamEdit',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/permissions/add', {
                name: 'teamPermissionAdd',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: PermissionsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/permissions', {
                name: 'teamPermissions',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: PermissionsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/permissions/:permission_id', {
                name: 'teamPermissionEdit',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: PermissionsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/users', {
                name: 'teamUsers',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: UsersList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/users/:user_id', {
                name: 'teamUserEdit',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: UsersEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/projects', {
                name: 'teamProjects',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/projects/add', {
                name: 'teamProjectAdd',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/projects/:project_id', {
                name: 'teamProjectEdit',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/credentials', {
                name: 'teamCredentials',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/credentials/add', {
                name: 'teamCredentialAdd',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:team_id/credentials/:credential_id', {
                name: 'teamCredentialEdit',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/credentials', {
                name: 'credentials',
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/credentials/add', {
                name: 'credentialAdd',
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/credentials/:credential_id', {
                name: 'credentialEdit',
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/users', {
                name: 'users',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/users/add', {
                name: 'userAdd',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/users/:user_id', {
                name: 'userEdit',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/users/:user_id/credentials', {
                name: 'userCredentials',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: CredentialsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/users/:user_id/permissions/add', {
                name: 'userPermissionAdd',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: PermissionsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/users/:user_id/permissions', {
                name: 'userPermissions',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: PermissionsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/users/:user_id/permissions/:permission_id', {
                name: 'userPermissionEdit',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: PermissionsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/users/:user_id/credentials/add', {
                name: 'userCredentialAdd',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/teams/:user_id/credentials/:credential_id', {
                name: 'teamUserCredentialEdit',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/login', {
                name: 'signIn',
                templateUrl: urlPrefix + 'partials/blank.html',
                controller: Authenticate
            }).

            when('/logout', {
                name: 'signOut',
                templateUrl: urlPrefix + 'partials/blank.html',
                controller: Authenticate,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/home', {
                name: 'dashboard',
                templateUrl: urlPrefix + 'partials/home.html',
                controller: Home,
                resolve: {
                    graphData: ['$q', 'jobStatusGraphData', 'hostCountGraphData', 'FeaturesService', function($q, jobStatusGraphData, hostCountGraphData, FeaturesService) {
                        return $q.all({
                            jobStatus: jobStatusGraphData.get("month", "all"),
                            hostCounts: hostCountGraphData.get(),
                            features: FeaturesService.get()
                        });
                    }]
                }
            }).

            when('/home/groups', {
                name: 'dashboardGroups',
                templateUrl: urlPrefix + 'partials/subhome.html',
                controller: HomeGroups,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/home/hosts', {
                name: 'dashboardHosts',
                templateUrl: urlPrefix + 'partials/subhome.html',
                controller: HomeHosts,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/license', {
                name: 'license',
                templateUrl: urlPrefix + 'partials/license.html',
                controller: LicenseController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            when('/sockets', {
                name: 'sockets',
                templateUrl: urlPrefix + 'partials/sockets.html',
                controller: SocketsController
            }).

            otherwise({
                redirectTo: '/home'
            });
        }
    ])

    .config(['$provide', function($provide) {
        $provide.decorator('$log', ['$delegate', function($delegate) {
            var _debug = $delegate.debug;
            $delegate.debug = function(msg) {
                // only show debug messages when debug_mode set to true in config
                if ($AnsibleConfig && $AnsibleConfig.debug_mode) {
                    _debug(msg);
                }
            };
            return $delegate;
        }]);
    }])

    .run(['$compile', '$cookieStore', '$rootScope', '$log', 'CheckLicense', '$location', 'Authorization', 'LoadBasePaths', 'Timer', 'ClearScope', 'HideStream', 'Socket',
        'LoadConfig', 'Store', 'ShowSocketHelp', 'AboutAnsibleHelp', 'ConfigureTower', 'CreateCustomInventory',
        function ($compile, $cookieStore, $rootScope, $log, CheckLicense, $location, Authorization, LoadBasePaths, Timer, ClearScope, HideStream, Socket,
        LoadConfig, Store, ShowSocketHelp, AboutAnsibleHelp, ConfigureTower, CreateCustomInventory) {


            var e, html, sock;

            function activateTab() {
                // Make the correct tab active
                var base = $location.path().replace(/^\//, '').split('/')[0];

                if (base === '') {
                    base = 'home';
                } else {
                    //base.replace(/\_/g, ' ');
                    base = (base === 'job_events' || base === 'job_host_summaries') ? 'jobs' : base;
                }
                //make sure that the tower icon works when not in portal mode
                $('.navbar-brand').attr('href', '/#/home');
                $rootScope.portalMode=false;
                if(base==='portal'){
                    $rootScope.portalMode= true;
                    //in portal mode we don't want the tower icon to lead anywhere
                    $('.navbar-brand').removeAttr('href');
                }

                $('#ansible-list-title').html('<strong>' + base.replace(/\_/,' ') + '</strong>');

                $('#ansible-main-menu li').each(function() {
                    $(this).removeClass('active');
                });
                $('#ansible-main-menu #' + base).addClass('active');
                // Apply to mobile menu as well
                $('#ansible-mobile-menu a').each(function() {
                    $(this).removeClass('active');
                });
                $('#ansible-mobile-menu a[href="#' + base + '"]').addClass('active');
            }

            if ($rootScope.removeConfigReady) {
                $rootScope.removeConfigReady();
            }
            $rootScope.removeConfigReady = $rootScope.$on('ConfigReady', function() {
                LoadBasePaths();

                $rootScope.breadcrumbs = [];
                $rootScope.crumbCache = [];
                $rootScope.sessionTimer = Timer.init();

                if ($rootScope.removeOpenSocket) {
                    $rootScope.removeOpenSocket();
                }
                $rootScope.removeOpenSocket = $rootScope.$on('OpenSocket', function() {
                    html = "<a href=\"\" ng-hide=\"socketStatus === 'ok'\" ng-click=\"socketHelp()\" aw-pop-over=\"{{ socketTip }}\" aw-pop-over-watch=\"socketTip\" data-placement=\"bottom\" data-trigger=\"hover\" " +
                    "data-popover-title=\"Live Events\" data-container=\"body\" style=\"font-size: 10px;\"><i class=\"fa icon-socket-{{ socketStatus }}\"></i></a>";
                    e = angular.element(document.getElementById('socket-beacon-div'));
                    e.empty().append(html);
                    $compile(e)($rootScope);

                    e = angular.element(document.getElementById('socket-beacon-li'));
                    e.empty().append(html);
                    $compile(e)($rootScope);

                    // Listen for job changes and issue callbacks to initiate
                    // DOM updates
                    function openSocket() {
                        var schedule_socket;

                        sock = Socket({ scope: $rootScope, endpoint: "jobs" });
                        sock.init();
                        sock.on("status_changed", function(data) {
                            $log.debug('Job ' + data.unified_job_id +
                                ' status changed to ' + data.status +
                                ' send to ' + $location.$$url);

                            // this acts as a router...it emits the proper
                            // value based on what URL the user is currently
                            // accessing.
                            if ($location.$$url === '/jobs') {
                                $rootScope.$emit('JobStatusChange-jobs', data);
                            } else if (/\/jobs\/(\d)+\/stdout/.test($location.$$url) ||
                                /\/ad_hoc_commands\/(\d)+/.test($location.$$url)) {
                                $log.debug("sending status to standard out");
                                $rootScope.$emit('JobStatusChange-jobStdout', data);
                            } else if (/\/jobs\/(\d)+/.test($location.$$url)) {
                                $rootScope.$emit('JobStatusChange-jobDetails', data);
                            } else if ($location.$$url === '/home') {
                                $rootScope.$emit('JobStatusChange-home', data);
                            } else if ($location.$$url === '/portal') {
                                $rootScope.$emit('JobStatusChange-portal', data);
                            } else if ($location.$$url === '/projects') {
                                $rootScope.$emit('JobStatusChange-projects', data);
                            } else if (/\/inventory\/(\d)+\/manage/.test($location.$$url)) {
                                $rootScope.$emit('JobStatusChange-inventory', data);
                            }
                        });
                        sock.on("summary_complete", function(data) {
                            $log.debug('Job summary_complete ' + data.unified_job_id);
                            $rootScope.$emit('JobSummaryComplete', data);
                        });

                        schedule_socket = Socket({
                            scope: $rootScope,
                            endpoint: "schedules"
                        });
                        schedule_socket.init();
                        schedule_socket.on("schedule_changed", function(data) {
                            $log.debug('Schedule  ' + data.unified_job_id + ' status changed to ' + data.status);
                            $rootScope.$emit('ScheduleStatusChange', data);
                        });
                    }
                    openSocket();

                    setTimeout(function() {
                        $rootScope.$apply(function() {
                            sock.checkStatus();
                            $log.debug('socket status: ' + $rootScope.socketStatus);
                        });
                    },2000);
                });

                $rootScope.$on("$routeChangeStart", function (event, next) {
                    // Before navigating away from current tab, make sure the primary view is visible
                    if ($('#stream-container').is(':visible')) {
                        HideStream();
                    }

                    // remove any lingering intervals
                    if ($rootScope.jobDetailInterval) {
                        window.clearInterval($rootScope.jobDetailInterval);
                    }
                    if ($rootScope.jobStdOutInterval) {
                        window.clearInterval($rootScope.jobStdOutInterval);
                    }

                    // On each navigation request, check that the user is logged in
                    if (!/^\/(login|logout)/.test($location.path())) {
                        // capture most recent URL, excluding login/logout
                        $rootScope.lastPath = $location.path();
                        $rootScope.enteredPath = $location.path();
                        $cookieStore.put('lastPath', $location.path());
                    }

                    if (Authorization.isUserLoggedIn() === false) {
                        if (next.templateUrl !== (urlPrefix + 'partials/login.html')) {
                            $location.path('/login');
                        }
                    } else if ($rootScope.sessionTimer.isExpired()) {
                      // gets here on timeout
                        if (next.templateUrl !== (urlPrefix + 'partials/login.html')) {
                            $rootScope.sessionTimer.expireSession();
                            if (sock) {
                                sock.socket.socket.disconnect();
                            }
                            $location.path('/login');
                        }
                    } else {
                        if ($rootScope.current_user === undefined || $rootScope.current_user === null) {
                            Authorization.restoreUserInfo(); //user must have hit browser refresh
                        }
                        if (next && next.$$route && (!/^\/(login|logout)/.test(next.$$route.originalPath))) {
                            // if not headed to /login or /logout, then check the license
                            CheckLicense.test();
                        }
                    }
                    activateTab();
                });

                if (!Authorization.getToken() || !Authorization.isUserLoggedIn()) {
                    // User not authenticated, redirect to login page
                    $rootScope.sessionExpired = false;
                    $cookieStore.put('sessionExpired', false);
                    $location.path('/login');
                } else {
                    // If browser refresh, set the user_is_superuser value
                    $rootScope.user_is_superuser = Authorization.getUserInfo('is_superuser');
                    // when the user refreshes we want to open the socket, except if the user is on the login page, which should happen after the user logs in (see the AuthService module for that call to OpenSocket)
                    if($location.$$url !== '/login'){
                        $rootScope.$emit('OpenSocket');
                    }
                }

                activateTab();

                $rootScope.viewAboutTower = function(){
                    AboutAnsibleHelp();
                };

                $rootScope.viewCurrentUser = function () {
                    $location.path('/users/' + $rootScope.current_user.id);
                };

                $rootScope.viewLicense = function () {
                    $location.path('/license');
                };
                $rootScope.toggleTab = function(e, tab, tabs) {
                    e.preventDefault();
                    $('#' + tabs + ' #' + tab).tab('show');
                };

                $rootScope.socketHelp = function() {
                    ShowSocketHelp();
                };

                $rootScope.leavePortal = function() {
                    $rootScope.portalMode=false;
                    $location.path('/home/');
                };

                $rootScope.configureTower = function(){
                    ConfigureTower({
                        scope: $rootScope,
                        parent_scope: $rootScope
                    });
                };

                $rootScope.createCustomInv = function(){
                    CreateCustomInventory({
                        parent_scope: $rootScope
                    });
                };

            }); // end of 'ConfigReady'


            if (!$AnsibleConfig) {
                // there may be time lag when loading the config file, so temporarily use what's in local storage
                $AnsibleConfig = Store('AnsibleConfig');
            }

            //the authorization controller redirects to the home page automatcially if there is no last path defined. in order to override
            // this, set the last path to /portal for instances where portal is visited for the first time.
            $rootScope.lastPath = ($location.path() === "/portal") ? 'portal' : undefined;

            LoadConfig();
        }
    ]);

export default tower;
