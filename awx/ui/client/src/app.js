/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// Vendor dependencies
import 'jquery';
import 'angular';
import 'bootstrap';
import 'jquery-ui';
import 'bootstrap-datepicker';
import 'jquery.resize';
import 'codemirror';
import 'js-yaml';
import 'select2';

// Configuration dependencies
global.$AnsibleConfig = null;

var urlPrefix;

if ($basePath) {
    urlPrefix = $basePath;
}

// Modules
import './helpers';
import './forms';
import './lists';
import './widgets';
import './help';
import './filters';
import { Home } from './controllers/Home';
import { SocketsController } from './controllers/Sockets';
import { CredentialsAdd, CredentialsEdit, CredentialsList } from './controllers/Credentials';
import { JobsListController } from './controllers/Jobs';
import portalMode from './portal-mode/main';
import systemTracking from './system-tracking/main';
import inventories from './inventories/main';
import inventoryScripts from './inventory-scripts/main';
import organizations from './organizations/main';
import permissions from './permissions/main';
import managementJobs from './management-jobs/main';
import jobDetail from './job-detail/main';
import jobSubmission from './job-submission/main';
import notifications from './notifications/main';
import access from './access/main';
import about from './about/main';
import license from './license/main';
import setupMenu from './setup-menu/main';
import mainMenu from './main-menu/main';
import breadCrumb from './bread-crumb/main';
import browserData from './browser-data/main';
import dashboard from './dashboard/main';
import moment from './shared/moment/main';
import templateUrl from './shared/template-url/main';
import login from './login/main';
import activityStream from './activity-stream/main';
import standardOut from './standard-out/main';
import JobTemplates from './job-templates/main';
import search from './search/main';
import credentials from './credentials/main';
import { ProjectsList, ProjectsAdd, ProjectsEdit } from './controllers/Projects';
import OrganizationsList from './organizations/list/organizations-list.controller';
import OrganizationsAdd from './organizations/add/organizations-add.controller';
import { UsersList, UsersAdd, UsersEdit } from './controllers/Users';
import { TeamsList, TeamsAdd, TeamsEdit } from './controllers/Teams';

import RestServices from './rest/main';
import './lookup/main';
import './shared/api-loader';
import './shared/form-generator';
import './shared/Modal';
import './shared/prompt-dialog';
import './shared/directives';
import './shared/filters';
import socket from './shared/socket/main';
import './shared/features/main';
import config from './shared/config/main';
import './login/authenticationServices/pendo/ng-pendo';
import footer from './footer/main';
import scheduler from './scheduler/main';

var tower = angular.module('Tower', [
    // how to add CommonJS / AMD  third-party dependencies:
    // 1. npm install --save package-name
    // 2. add package name to ./grunt-tasks/webpack.vendorFiles
    require('angular-breadcrumb'),
    require('angular-codemirror'),
    require('angular-cookies'),
    require('angular-drag-and-drop-lists'),
    require('angular-ui-router'),
    require('angular-sanitize'),
    require('angular-scheduler').name,
    require('angular-tz-extensions'),
    require('lr-infinite-scroll'),
    require('ng-toast'),


    about.name,
    license.name,
    RestServices.name,
    browserData.name,
    systemTracking.name,
    inventories.name,
    inventoryScripts.name,
    organizations.name,
    permissions.name,
    managementJobs.name,
    setupMenu.name,
    mainMenu.name,
    breadCrumb.name,
    dashboard.name,
    moment.name,
    templateUrl.name,
    login.name,
    activityStream.name,
    footer.name,
    jobDetail.name,
    jobSubmission.name,
    notifications.name,
    standardOut.name,
    access.name,
    JobTemplates.name,
    portalMode.name,
    search.name,
    config.name,
    credentials.name,
    //'templates',
    'Utilities',
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
    'StreamWidget',
    'JobsHelper',
    'CredentialsHelper',
    'StreamListDefinition',
    'ActivityDetailDefinition',
    'VariablesHelper',
    'SchedulesListDefinition',
    'ScheduledJobsDefinition',
    //'Timezones',
    'SchedulesHelper',
    'JobsListDefinition',
    'LogViewerStatusDefinition',
    'StandardOutHelper',
    'LogViewerOptionsDefinition',
    'JobDetailHelper',
    'socket',
    'lrInfiniteScroll',
    'LoadConfigHelper',
    'PortalJobsListDefinition',
    'features',
    'longDateFilter',
    'pendolytics',
    scheduler.name,
    'ApiModelHelper',
    'ActivityStreamHelper',
])

.constant('AngularScheduler.partials', urlPrefix + 'lib/angular-scheduler/lib/')
    .constant('AngularScheduler.useTimezone', true)
    .constant('AngularScheduler.showUTCField', true)
    .constant('$timezones.definitions.location', urlPrefix + 'lib/angular-tz-extensions/tz/data')
    .config(['$pendolyticsProvider', function($pendolyticsProvider) {
        $pendolyticsProvider.doNotAutoStart();
    }])
    .config(['ngToastProvider', function(ngToastProvider) {
        ngToastProvider.configure({
            animation: 'slide',
            dismissOnTimeout: true,
            timeout: 4000
        });
    }])
    .config(['$stateProvider', '$urlRouterProvider', '$breadcrumbProvider',
        '$urlMatcherFactoryProvider',
        function($stateProvider, $urlRouterProvider, $breadcrumbProvider,
            $urlMatcherFactoryProvider) {
            $urlMatcherFactoryProvider.strictMode(false);
            $breadcrumbProvider.setOptions({
                templateUrl: urlPrefix + 'partials/breadcrumb.html'
            });

            // route to the details pane of /job/:id/host-event/:eventId if no other child specified
            $urlRouterProvider.when('/jobs/*/host-event/*', '/jobs/*/host-event/*/details');

            // $urlRouterProvider.otherwise("/home");
            $urlRouterProvider.otherwise(function($injector) {
                var $state = $injector.get("$state");
                $state.go('dashboard');
            });

            $stateProvider.
            state('dashboard', {
                url: '/home',
                templateUrl: urlPrefix + 'partials/home.html',
                controller: Home,
                params: { licenseMissing: null },
                data: {
                    activityStream: true,
                    refreshButton: true
                },
                ncyBreadcrumb: {
                    label: "DASHBOARD"
                },
                resolve: {
                    graphData: ['$q', 'jobStatusGraphData', '$rootScope',
                        function($q, jobStatusGraphData, $rootScope) {
                            return $rootScope.featuresConfigured.promise.then(function() {
                                return $q.all({
                                    jobStatus: jobStatusGraphData.get("month", "all"),
                                });
                            });
                        }
                    ]
                }
            }).

            state('jobs', {
                url: '/jobs',
                templateUrl: urlPrefix + 'partials/jobs.html',
                controller: JobsListController,
                ncyBreadcrumb: {
                    label: "JOBS"
                }
            }).

            state('projects', {
                url: '/projects?{status}',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsList,
                data: {
                    activityStream: true,
                    activityStreamTarget: 'project'
                },
                ncyBreadcrumb: {
                    label: "PROJECTS"
                }
            }).

            state('projects.add', {
                url: '/add',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsAdd,
                ncyBreadcrumb: {
                    parent: "projects",
                    label: "CREATE PROJECT"
                }
            }).

            state('projects.edit', {
                url: '/:id',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsEdit,
                data: {
                    activityStreamId: 'id'
                },
                ncyBreadcrumb: {
                    parent: 'projects',
                    label: '{{name}}'
                }
            }).

            state('projectOrganizations', {
                url: '/projects/:project_id/organizations',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: OrganizationsList
            }).

            state('projectOrganizationAdd', {
                url: '/projects/:project_id/organizations/add',
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: OrganizationsAdd
            }).

            state('teams', {
                url: '/teams',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsList,
                data: {
                    activityStream: true,
                    activityStreamTarget: 'team'
                },
                ncyBreadcrumb: {
                    parent: 'setup',
                    label: 'TEAMS'
                }
            }).

            state('teams.add', {
                url: '/add',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsAdd,
                ncyBreadcrumb: {
                    parent: "teams",
                    label: "CREATE TEAM"
                }
            }).

            state('teams.edit', {
                url: '/:team_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsEdit,
                data: {
                    activityStreamId: 'team_id'
                },
                ncyBreadcrumb: {
                    parent: "teams",
                    label: "{{team_obj.name}}"
                }
            }).

            state('teamUsers', {
                url: '/teams/:team_id/users',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: UsersList
            }).

            state('teamUserEdit', {
                url: '/teams/:team_id/users/:user_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: UsersEdit
            }).

            state('teamProjects', {
                url: '/teams/:team_id/projects',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsList
            }).

            state('teamProjectAdd', {
                url: '/teams/:team_id/projects/add',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsAdd
            }).

            state('teamProjectEdit', {
                url: '/teams/:team_id/projects/:project_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsEdit
            }).

            state('teamCredentials', {
                url: '/teams/:team_id/credentials',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsList
            }).

            state('teamCredentialAdd', {
                url: '/teams/:team_id/credentials/add',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsAdd
            }).

            state('teamCredentialEdit', {
                url: '/teams/:team_id/credentials/:credential_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsEdit
            }).

            state('credentials', {
                url: '/credentials',
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsList,
                data: {
                    activityStream: true,
                    activityStreamTarget: 'credential'
                },
                ncyBreadcrumb: {
                    parent: 'setup',
                    label: 'CREDENTIALS'
                }
            }).

            state('credentials.add', {
                url: '/add',
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsAdd,
                ncyBreadcrumb: {
                    parent: "credentials",
                    label: "CREATE CREDENTIAL"
                }
            }).

            state('credentials.edit', {
                url: '/:credential_id',
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsEdit,
                data: {
                    activityStreamId: 'credential_id'
                },
                ncyBreadcrumb: {
                    parent: "credentials",
                    label: "{{credential_obj.name}}"
                }
            }).

            state('users', {
                url: '/users',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersList,
                data: {
                    activityStream: true,
                    activityStreamTarget: 'user'
                },
                ncyBreadcrumb: {
                    parent: 'setup',
                    label: 'USERS'
                }
            }).

            state('users.add', {
                url: '/add',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersAdd,
                ncyBreadcrumb: {
                    parent: "users",
                    label: "CREATE USER"
                }
            }).

            state('users.edit', {
                url: '/:user_id',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersEdit,
                data: {
                    activityStreamId: 'user_id'
                },
                ncyBreadcrumb: {
                    parent: "users",
                    label: "{{user_obj.username}}"
                }
            }).

            state('userCredentials', {
                url: '/users/:user_id/credentials',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: CredentialsList
            }).

            state('userCredentialAdd', {
                url: '/users/:user_id/credentials/add',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsAdd
            }).

            state('teamUserCredentialEdit', {
                url: '/teams/:user_id/credentials/:credential_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsEdit
            }).

            state('sockets', {
                url: '/sockets',
                templateUrl: urlPrefix + 'partials/sockets.html',
                controller: SocketsController,
                ncyBreadcrumb: {
                    label: 'SOCKETS'
                }
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

.run(['$q', '$compile', '$cookieStore', '$rootScope', '$log',
    'CheckLicense', '$location', 'Authorization', 'LoadBasePaths', 'Timer',
    'ClearScope', 'LoadConfig', 'Store',
    'pendoService', 'Prompt', 'Rest', 'Wait',
    'ProcessErrors', '$state', 'GetBasePath', 'ConfigService',
    'FeaturesService', '$filter', 'SocketService',
    function($q, $compile, $cookieStore, $rootScope, $log, CheckLicense,
        $location, Authorization, LoadBasePaths, Timer, ClearScope,
        LoadConfig, Store, pendoService, Prompt, Rest, Wait,
        ProcessErrors, $state, GetBasePath, ConfigService, FeaturesService,
        $filter, SocketService) {
        var sock;
        $rootScope.addPermission = function(scope) {
            $compile("<add-permissions class='AddPermissions'></add-permissions>")(scope);
        };
        $rootScope.addPermissionWithoutTeamTab = function(scope) {
            $compile("<add-permissions class='AddPermissions' without-team-permissions='true'></add-permissions>")(scope);
        };

        $rootScope.deletePermission = function(user, accessListEntry) {
            let entry = accessListEntry;

            let action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');

                let url;
                if (entry.team_id) {
                    url = GetBasePath("teams") + entry.team_id + "/roles/";
                } else {
                    url = GetBasePath("users") + user.id + "/roles/";
                }

                Rest.setUrl(url);
                Rest.post({ "disassociate": true, "id": entry.id })
                    .success(function() {
                        Wait('stop');
                        $rootScope.$broadcast("refreshList", "permission");
                    })
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to remove access.  Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            if (accessListEntry.team_id) {
                Prompt({
                    hdr: `Team access removal`,
                    body: `<div class="Prompt-bodyQuery">Please confirm that you would like to remove <span class="Prompt-emphasis">${entry.name}</span> access from the team <span class="Prompt-emphasis">${$filter('sanitize')(entry.team_name)}</span>. This will affect all members of the team. If you would like to only remove access for this particular user, please remove them from the team.</div>`,
                    action: action,
                    actionText: 'REMOVE TEAM ACCESS'
                });
            } else {
                Prompt({
                    hdr: `User access removal`,
                    body: `<div class="Prompt-bodyQuery">Please confirm that you would like to remove <span class="Prompt-emphasis">${entry.name}</span> access from <span class="Prompt-emphasis">${user.username}</span>.</div>`,
                    action: action,
                    actionText: 'REMOVE'
                });
            }
        };

        $rootScope.deletePermissionFromUser = function(userId, userName, roleName, roleType, url) {
            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                Rest.setUrl(url);
                Rest.post({ "disassociate": true, "id": userId })
                    .success(function() {
                        Wait('stop');
                        $rootScope.$broadcast("refreshList", "permission");
                    })
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Could not disassociate user from role.  Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: `Remove role`,
                body: `
                        <div class="Prompt-bodyQuery">
                            Confirm  the removal of the ${roleType}
                                <span class="Prompt-emphasis"> ${roleName} </span>
                            role associated with ${userName}.
                        </div>
                    `,
                action: action,
                actionText: 'REMOVE'
            });
        };

        $rootScope.deletePermissionFromTeam = function(teamId, teamName, roleName, roleType, url) {
            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                Rest.setUrl(url);
                Rest.post({ "disassociate": true, "id": teamId })
                    .success(function() {
                        Wait('stop');
                        $rootScope.$broadcast("refreshList", "role");
                    })
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Could not disassociate team from role.  Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            Prompt({
                hdr: `Remove role`,
                body: `
                        <div class="Prompt-bodyQuery">
                            Confirm  the removal of the ${roleType}
                                <span class="Prompt-emphasis"> ${roleName} </span>
                            role associated with the ${teamName} team.
                        </div>
                    `,
                action: action,
                actionText: 'REMOVE'
            });
        };

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
            $rootScope.portalMode = false;
            if (base === 'portal') {
                $rootScope.portalMode = true;
                //in portal mode we don't want the tower icon to lead anywhere
                $('.navbar-brand').removeAttr('href');
            }

            $('#ansible-list-title').html('<strong>' + base.replace(/\_/, ' ') + '</strong>');

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
            var list, id;
            // initially set row edit indicator for crud pages
            if ($location.$$path && $location.$$path.split("/")[3] && $location.$$path.split("/")[3] === "schedules") {
                list = $location.$$path.split("/")[3];
                id = $location.$$path.split("/")[4];
                $rootScope.listBeingEdited = list;
                $rootScope.rowBeingEdited = id;
                $rootScope.initialIndicatorLoad = true;
            } else if ($location.$$path.split("/")[2]) {
                list = $location.$$path.split("/")[1];
                id = $location.$$path.split("/")[2];
                $rootScope.listBeingEdited = list;
                $rootScope.rowBeingEdited = id;
            }

            LoadBasePaths();

            $rootScope.crumbCache = [];

            if ($rootScope.removeOpenSocket) {
                $rootScope.removeOpenSocket();
            }
            $rootScope.removeOpenSocket = $rootScope.$on('OpenSocket', function() {
                function openSocket() {
                    $rootScope.socket = Socket({ scope: $rootScope});
                    $rootScope.socket.init();
                    // $rootScope.socket.on("status_changed", function(data) {
                    //     $log.debug('Job ' + data.unified_job_id +
                    //         ' status changed to ' + data.status +
                    //         ' send to ' + $location.$$url);
                    //
                    //     // this acts as a router...it emits the proper
                    //     // value based on what URL the user is currently
                    //     // accessing.
                    //     if ($state.is('jobs')) {
                    //         $rootScope.$emit('JobStatusChange-jobs', data);
                    //     } else if ($state.includes('jobDetail') ||
                    //         $state.is('adHocJobStdout') ||
                    //         $state.is('inventorySyncStdout') ||
                    //         $state.is('managementJobStdout') ||
                    //         $state.is('scmUpdateStdout')) {
                    //
                    //         $log.debug("sending status to standard out");
                    //         $rootScope.$emit('JobStatusChange-jobStdout', data);
                    //     }
                    //     if ($state.includes('jobDetail')) {
                    //         $rootScope.$emit('JobStatusChange-jobDetails', data);
                    //     } else if ($state.is('dashboard')) {
                    //         $rootScope.$emit('JobStatusChange-home', data);
                    //     } else if ($state.is('portalMode')) {
                    //         $rootScope.$emit('JobStatusChange-portal', data);
                    //     } else if ($state.is('projects')) {
                    //         $rootScope.$emit('JobStatusChange-projects', data);
                    //     } else if ($state.is('inventoryManage')) {
                    //         $rootScope.$emit('JobStatusChange-inventory', data);
                    //     }
                    // });
                    // $rootScope.socket.on("summary_complete", function(data) {
                    //     $log.debug('Job summary_complete ' + data.unified_job_id);
                    //     $rootScope.$emit('JobSummaryComplete', data);
                    // });

                    // schedule_socket = Socket({
                    //     scope: $rootScope,
                    //     endpoint: "schedules"
                    // });
                    // schedule_socket.init();
                    // $rootScope.socket.on("schedule_changed", function(data) {
                    //     $log.debug('Schedule  ' + data.unified_job_id + ' status changed to ' + data.status);
                    //     $rootScope.$emit('ScheduleStatusChange', data);
                    // });

                    // control_socket = Socket({
                    //     scope: $rootScope,
                    //     endpoint: "control"
                    // });
                    // control_socket.init();
                    // $rootScope.socket.on("limit_reached", function(data) {
                    //     $log.debug(data.reason);
                    //     $rootScope.sessionTimer.expireSession('session_limit');
                    //     $state.go('signOut');
                    // });
                }
                openSocket();

                setTimeout(function() {
                    $rootScope.$apply(function() {
                        $rootScope.socket.checkStatus();
                        $log.debug('socket status: ' + $rootScope.socketStatus);
                    });
                }, 2000);
            });
            // {'groups':
            //      {'jobs': ['status_changed', 'summary'],
            //       'schedules': ['changed'],
            //       'ad_hoc_command_events': [ids,],
            //       'job_events': [ids,],
            //       'control': ['limit_reached'],
            //      }
            // }
            $rootScope.$on('$stateChangeStart', function(event, toState, toParams, fromState) {
                if(toState.name === 'dashboard'){
                    SocketService.emit('{"groups":{"jobs": ["status_changed"]}}');
                    console.log(toState.name);
                }
                else if(toState.name === 'jobDetail'){
                    SocketService.emit(`{"groups":{"jobs": ["status_changed", "summary"] , "job_events":[${toParams.id}]}}`);
                    console.log(toState.name);
                }
                else if(toState.name === 'jobStdout'){
                    SocketService.emit('{"groups":{"jobs": ["status_changed"]}}');
                    console.log(toState.name);
                }
                else if(toState.name === 'jobs'){
                    SocketService.emit('{"groups":{"jobs": ["status_changed"] , "schedules": ["changed"]}}');
                    console.log(toState.name);
                }
                else if(toState.name === 'portalMode'){
                    SocketService.emit('{"groups":{"jobs": ["status_changed"]}}');
                    console.log(toState.name);
                }
                else if(toState.name === 'projects'){
                    SocketService.emit('{"groups":{"jobs": ["status_changed"]}}');
                    console.log(toState.name);
                }
                else if(toState.name === 'inventory'){
                    SocketService.emit('{"groups":{"jobs": ["status_changed"]}}');
                    console.log(toState.name);
                }
                else if(toState.name === 'adHocJobStdout'){
                    SocketService.emit(`{"groups":{"ad_hoc_command_events": [${toParams.id}]}}`);
                    console.log(toState.name);
                }
            });

            $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState) {

                if (fromState.name === 'license' && toParams.hasOwnProperty('licenseMissing')) {
                    $rootScope.licenseMissing = toParams.licenseMissing;
                }
                var list, id;
                // broadcast event change if editing crud object
                if ($location.$$path && $location.$$path.split("/")[3] && $location.$$path.split("/")[3] === "schedules") {
                    list = $location.$$path.split("/")[3];
                    id = $location.$$path.split("/")[4];

                    if (!$rootScope.initialIndicatorLoad) {
                        delete $rootScope.listBeingEdited;
                        delete $rootScope.rowBeingEdited;
                    } else {
                        delete $rootScope.initialIndicatorLoad;
                    }

                    $rootScope.$broadcast("EditIndicatorChange", list, id);
                } else if ($location.$$path.split("/")[2]) {
                    list = $location.$$path.split("/")[1];
                    id = $location.$$path.split("/")[2];

                    delete $rootScope.listBeingEdited;
                    delete $rootScope.rowBeingEdited;

                    $rootScope.$broadcast("EditIndicatorChange", list, id);
                } else if ($rootScope.addedAnItem) {
                    delete $rootScope.addedAnItem;
                    $rootScope.$broadcast("RemoveIndicator");
                } else {
                    $rootScope.$broadcast("RemoveIndicator");
                }
            });

            if (!Authorization.getToken() || !Authorization.isUserLoggedIn()) {
                // User not authenticated, redirect to login page
                $location.path('/login');
            } else {
                var lastUser = $cookieStore.get('current_user'),
                    timestammp = Store('sessionTime');
                if (lastUser && lastUser.id && timestammp && timestammp[lastUser.id] && timestammp[lastUser.id].loggedIn) {
                    var stime = timestammp[lastUser.id].time,
                        now = new Date().getTime();
                    if ((stime - now) <= 0) {
                        $location.path('/login');
                    }
                }
                // If browser refresh, set the user_is_superuser value
                $rootScope.user_is_superuser = Authorization.getUserInfo('is_superuser');
                $rootScope.user_is_system_auditor = Authorization.getUserInfo('is_system_auditor');

                // state the user refreshes we want to open the socket, except if the user is on the login page, which should happen after the user logs in (see the AuthService module for that call to OpenSocket)
                if (!_.contains($location.$$url, '/login')) {
                    ConfigService.getConfig().then(function() {
                        Timer.init().then(function(timer) {
                            $rootScope.sessionTimer = timer;
                            // $rootScope.$emit('OpenSocket');
                            SocketService.init();
                            pendoService.issuePendoIdentity();
                            CheckLicense.test();
                            FeaturesService.get();
                            if ($location.$$path === "/home" && $state.current && $state.current.name === "") {
                                $state.go('dashboard');
                            } else if ($location.$$path === "/portal" && $state.current && $state.current.name === "") {
                                $state.go('portalMode');
                            }
                        });
                    });
                }
            }

            activateTab();

            $rootScope.viewCurrentUser = function() {
                $location.path('/users/' + $rootScope.current_user.id);
            };

            $rootScope.viewLicense = function() {
                $location.path('/license');
            };
            $rootScope.toggleTab = function(e, tab, tabs) {
                e.preventDefault();
                $('#' + tabs + ' #' + tab).tab('show');
            };

            $rootScope.leavePortal = function() {
                $rootScope.portalMode = false;
                $location.path('/home/');
            };

        }); // end of 'ConfigReady'


        if (!$AnsibleConfig) {
            // create a promise that will resolve state $AnsibleConfig is loaded
            $rootScope.loginConfig = $q.defer();
        }
        if (!$rootScope.featuresConfigured) {
            // create a promise that will resolve when features are loaded
            $rootScope.featuresConfigured = $q.defer();
        }
        $rootScope.licenseMissing = true;
        //the authorization controller redirects to the home page automatcially if there is no last path defined. in order to override
        // this, set the last path to /portal for instances where portal is visited for the first time.
        $rootScope.lastPath = ($location.path() === "/portal") ? 'portal' : undefined;

        LoadConfig();
    }
]);

export default tower;
