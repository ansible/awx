/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/



var urlPrefix;

if ($basePath) {
    urlPrefix = $basePath;
} else {
    // required to make tests work
    var $basePath = '/static/';
    urlPrefix = $basePath;
}

import './helpers';
import './forms';
import './lists';
import './widgets';
import './help';
import './filters';
import {Home, HomeGroups, HomeHosts} from './controllers/Home';
import {SocketsController} from './controllers/Sockets';
import {CredentialsAdd, CredentialsEdit, CredentialsList} from './controllers/Credentials';
import {JobsListController} from './controllers/Jobs';
import {PortalController} from './controllers/Portal';
import systemTracking from './system-tracking/main';
import inventoryScripts from './inventory-scripts/main';
import permissions from './permissions/main';
import managementJobs from './management-jobs/main';
import routeExtensions from './shared/route-extensions/main';
import breadcrumbs from './shared/breadcrumbs/main';


// modules
import setupMenu from './setup-menu/main';
import mainMenu from './main-menu/main';
import breadCrumb from './bread-crumb/main';
import browserData from './browser-data/main';
import dashboard from './dashboard/main';
import moment from './shared/moment/main';
import templateUrl from './shared/template-url/main';
import adhoc from './adhoc/main';
import login from './login/main';
import {JobDetailController} from './controllers/JobDetail';
import {JobStdoutController} from './controllers/JobStdout';
import {JobTemplatesList, JobTemplatesAdd, JobTemplatesEdit} from './controllers/JobTemplates';
import {LicenseController} from './controllers/License';
import {ScheduleEditController} from './controllers/Schedules';
import {ProjectsList, ProjectsAdd, ProjectsEdit} from './controllers/Projects';
import {OrganizationsList, OrganizationsAdd, OrganizationsEdit} from './controllers/Organizations';
import {InventoriesList, InventoriesAdd, InventoriesEdit, InventoriesManage} from './controllers/Inventories';
import {AdminsList} from './controllers/Admins';
import {UsersList, UsersAdd, UsersEdit} from './controllers/Users';
import {TeamsList, TeamsAdd, TeamsEdit} from './controllers/Teams';

import RestServices from './rest/main';
import './shared/api-loader';
import './shared/form-generator';
import './shared/Modal';
import './shared/prompt-dialog';
import './shared/directives';
import './shared/filters';
import './shared/InventoryTree';
import './shared/Socket';
import './job-templates/main';
import './shared/features/main';
import './login/authenticationServices/pendo/ng-pendo';
import footer from './footer/main';

/*#if DEBUG#*/
import {__deferLoadIfEnabled} from './debug';
__deferLoadIfEnabled();
/*#endif#*/

var tower = angular.module('Tower', [
    // 'ngAnimate',
    'ngRoute',
    'ngSanitize',
    'ngCookies',
    RestServices.name,
    // routeExtensions.name,
    browserData.name,
    breadcrumbs.name,
    systemTracking.name,
    inventoryScripts.name,
    permissions.name,
    managementJobs.name,
    setupMenu.name,
    mainMenu.name,
    breadCrumb.name,
    dashboard.name,
    moment.name,
    templateUrl.name,
    adhoc.name,
    login.name,
    footer.name,
    'templates',
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
    'AWDirectives',
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
    'CompletedJobsDefinition',
    'AllJobsDefinition',
    'JobFormDefinition',
    'JobSummaryDefinition',
    'ParseHelper',
    'ChildrenHelper',
    'ProjectPathHelper',
    'md5Helper',
    'SelectionHelper',
    'HostGroupsFormDefinition',
    'PortalJobsWidget',
    'StreamWidget',
    'JobsHelper',
    'InventoryGroupsHelpDefinition',
    'InventoryTree',
    'CredentialsHelper',
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
    'JobDetailHelper',
    'SocketIO',
    'lrInfiniteScroll',
    'LoadConfigHelper',
    'SocketHelper',
    'AboutAnsibleHelpModal',
    'PortalJobsListDefinition',
    'features',
    'longDateFilter',
    'pendolytics',
    'ui.router'
])

    .constant('AngularScheduler.partials', urlPrefix + 'lib/angular-scheduler/lib/')
    .constant('AngularScheduler.useTimezone', true)
    .constant('AngularScheduler.showUTCField', true)
    .constant('$timezones.definitions.location', urlPrefix + 'lib/angular-tz-extensions/tz/data')
    .config(['$pendolyticsProvider', function($pendolyticsProvider) {
        $pendolyticsProvider.doNotAutoStart();
    }])
    .config(['$stateProvider', '$urlRouterProvider',
        function ($stateProvider, $urlRouterProvider) {

            $urlRouterProvider.otherwise("/home");

            $stateProvider.
            state('jobs', {
                url: '/jobs',
                templateUrl: urlPrefix + 'partials/jobs.html',
                controller: JobsListController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('portal', {
                url: '/portal',
                templateUrl: urlPrefix + 'partials/portal.html',
                controller: PortalController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('jobDetail', {
                url: '/jobs/:id',
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

            state('jobsStdout', {
                url: '/jobs/:id/stdout',
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

            state('adHocJobStdout', {
                url: '/ad_hoc_commands/:id',
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

            state('jobTemplates', {
                url: '/job_templates',
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('jobTemplateAdd', {
                url: '/job_templates/add',
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('jobTemplateEdit', {
                url: '/job_templates/:template_id',
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('jobTemplateSchedules', {
                url: '/job_templates/:id/schedules',
                templateUrl: urlPrefix + 'partials/schedule_detail.html',
                controller: ScheduleEditController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('projects', {
                url: '/projects',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('projectAdd', {
                url: '/projects/add',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('projectEdit', {
                url: '/projects/:id',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('projectSchedules', {
                url: '/projects/:id/schedules',
                templateUrl: urlPrefix + 'partials/schedule_detail.html',
                controller: ScheduleEditController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('projectOrganizations', {
                url: '/projects/:project_id/organizations',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: OrganizationsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('projectOrganizationAdd', {
                url: '/projects/:project_id/organizations/add',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: OrganizationsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('inventories', {
                url: '/inventories',
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: InventoriesList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('inventoryAdd', {
                url: '/inventories/add',
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: InventoriesAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('inventoryEdit', {
                url: '/inventories/:inventory_id',
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: InventoriesEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('inventoryJobTemplateAdd', {
                url: '/inventories/:inventory_id/job_templates/add',
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            // state('/inventories/:inventory_id/job_templates/', {
            //     redirectTo: '/inventories/:inventory_id'
            // }).
            //
            state('inventoryJobTemplateEdit', {
                url: '/inventories/:inventory_id/job_templates/:template_id',
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('inventoryManage', {
                url: '/inventories/:inventory_id/manage?groups',
                templateUrl: urlPrefix + 'partials/inventory-manage.html',
                controller: InventoriesManage,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('organizations', {
                url: '/organizations',
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: OrganizationsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('organizationsAdd', {
                url: '/organization/add',
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: OrganizationsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('organizationEdit', {
                url: '/organizations/:organization_id',
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: OrganizationsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('organizationAdmins', {
                url: '/organizations/:organization_id/admins',
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: AdminsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('organizationUsers', {
                url:'/organizations/:organization_id/users',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('organizationUserAdd', {
                url: '/organizations/:organization_id/users/add',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('organizationUserEdit', {
                url: '/organizations/:organization_id/users/:user_id',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teams', {
                url: '/teams',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamsAdd', {
                url: '/teams/add',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamEdit', {
                url: '/teams/:team_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamUsers', {
                url: '/teams/:team_id/users',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: UsersList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamUserEdit', {
                url: '/teams/:team_id/users/:user_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: UsersEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamProjects', {
                url: '/teams/:team_id/projects',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamProjectAdd', {
                url: '/teams/:team_id/projects/add',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamProjectEdit', {
                url: '/teams/:team_id/projects/:project_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamCredentials', {
                url: '/teams/:team_id/credentials',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamCredentialAdd', {
                url: '/teams/:team_id/credentials/add',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamCredentialEdit', {
                url: '/teams/:team_id/credentials/:credential_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('credentials', {
                url: '/credentials',
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('credentialAdd', {
                url: '/credentials/add',
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('credentialEdit', {
                url: '/credentials/:credential_id',
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('users', {
                url: '/users',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('userAdd', {
                url: '/users/add',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('userEdit', {
                url: '/users/:user_id',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('userCredentials', {
                url: '/users/:user_id/credentials',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: CredentialsList,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('userCredentialAdd', {
                url: '/users/:user_id/credentials/add',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsAdd,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('teamUserCredentialEdit', {
                url: '/teams/:user_id/credentials/:credential_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsEdit,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('dashboard', {
                url: '/home',
                templateUrl: urlPrefix + 'partials/home.html',
                controller: Home,
                resolve: {
                    graphData: ['$q', 'jobStatusGraphData', 'FeaturesService', function($q, jobStatusGraphData, FeaturesService) {
                        return $q.all({
                            jobStatus: jobStatusGraphData.get("month", "all"),
                            features: FeaturesService.get()
                        });
                    }]
                }
            }).

            state('dashboardGroups', {
                url: '/home/groups',
                templateUrl: urlPrefix + 'partials/subhome.html',
                controller: HomeGroups,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('dashboardHosts', {
                url: '/home/hosts?has_active_failures',
                templateUrl: urlPrefix + 'partials/subhome.html',
                controller: HomeHosts,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('license', {
                url: '/license',
                templateUrl: urlPrefix + 'partials/license.html',
                controller: LicenseController,
                resolve: {
                    features: ['FeaturesService', function(FeaturesService) {
                        return FeaturesService.get();
                    }]
                }
            }).

            state('sockets', {
                url: '/sockets',
                templateUrl: urlPrefix + 'partials/sockets.html',
                controller: SocketsController
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

    .run(['$q', '$compile', '$cookieStore', '$rootScope', '$log', 'CheckLicense', '$location', 'Authorization', 'LoadBasePaths', 'Timer', 'ClearScope', 'HideStream', 'Socket',
        'LoadConfig', 'Store', 'ShowSocketHelp', 'AboutAnsibleHelp', 'pendoService',
        function ($q, $compile, $cookieStore, $rootScope, $log, CheckLicense, $location, Authorization, LoadBasePaths, Timer, ClearScope, HideStream, Socket,
        LoadConfig, Store, ShowSocketHelp, AboutAnsibleHelp, pendoService) {


            var sock;

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

                if ($rootScope.removeOpenSocket) {
                    $rootScope.removeOpenSocket();
                }
                $rootScope.removeOpenSocket = $rootScope.$on('OpenSocket', function() {
                    // Listen for job changes and issue callbacks to initiate
                    // DOM updates
                    function openSocket() {
                        var schedule_socket, control_socket;

                        sock = Socket({ scope: $rootScope, endpoint: "jobs" });
                        sock.init();
                        sock.on("status_changed", function(data) {
                            $log.debug('Job ' + data.unified_job_id +
                                ' status changed to ' + data.status +
                                ' send to ' + $location.$$url);

                            var urlToCheck = $location.$$url;
                            if (urlToCheck.indexOf("?") !== -1) {
                                urlToCheck = urlToCheck.substr(0, urlToCheck.indexOf("?"));
                            }

                            // this acts as a router...it emits the proper
                            // value based on what URL the user is currently
                            // accessing.
                            if (urlToCheck === '/jobs') {
                                $rootScope.$emit('JobStatusChange-jobs', data);
                            } else if (/\/jobs\/(\d)+\/stdout/.test(urlToCheck) ||
                                /\/ad_hoc_commands\/(\d)+/.test(urlToCheck)) {
                                $log.debug("sending status to standard out");
                                $rootScope.$emit('JobStatusChange-jobStdout', data);
                            } else if (/\/jobs\/(\d)+/.test(urlToCheck)) {
                                $rootScope.$emit('JobStatusChange-jobDetails', data);
                            } else if (urlToCheck === '/home') {
                                $rootScope.$emit('JobStatusChange-home', data);
                            } else if (urlToCheck === '/portal') {
                                $rootScope.$emit('JobStatusChange-portal', data);
                            } else if (urlToCheck === '/projects') {
                                $rootScope.$emit('JobStatusChange-projects', data);
                            } else if (/\/inventories\/(\d)+\/manage/.test(urlToCheck)) {
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

                        control_socket = Socket({
                            scope: $rootScope,
                            endpoint: "control"
                        });
                        control_socket.init();
                        control_socket.on("limit_reached", function(data) {
                            $log.debug(data.reason);
                            $rootScope.sessionTimer.expireSession('session_limit');
                            $location.url('/login');
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

                $rootScope.$on("$stateChangeStart", function (event, next, nextParams, prev) {
                    // this line removes the query params attached to a route
                    if(prev && prev.$$route &&
                        prev.$$route.name === 'systemTracking'){
                            $location.replace($location.search('').$$url);
                    }

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
                        if (next.templateUrl !== (urlPrefix + 'login/loginBackDrop.partial.html')) {
                            $location.path('/login');
                        }
                    } else if ($rootScope && $rootScope.sessionTimer && $rootScope.sessionTimer.isExpired()) {
                      // gets here on timeout
                        if (next.templateUrl !== (urlPrefix + 'login/loginBackDrop.partial.html')) {
                            $rootScope.sessionTimer.expireSession('idle');
                            if (sock&& sock.socket && sock.socket.socket) {
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
                    // state the user refreshes we want to open the socket, except if the user is on the login page, which should happen after the user logs in (see the AuthService module for that call to OpenSocket)
                    if(!_.contains($location.$$url, '/login')){
                        Timer.init().then(function(timer){
                            $rootScope.sessionTimer = timer;
                            $rootScope.$emit('OpenSocket');
                            pendoService.issuePendoIdentity();
                        });
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

            }); // end of 'ConfigReady'


            if (!$AnsibleConfig) {
                // create a promise that will resolve state $AnsibleConfig is loaded
                $rootScope.loginConfig = $q.defer();
            }

            //the authorization controller redirects to the home page automatcially if there is no last path defined. in order to override
            // this, set the last path to /portal for instances where portal is visited for the first time.
            $rootScope.lastPath = ($location.path() === "/portal") ? 'portal' : undefined;

            LoadConfig();
        }
    ]);

export default tower;
