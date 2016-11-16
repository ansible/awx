/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// Vendor dependencies
import 'jquery';
import 'angular';
import 'angular-gettext';
import 'bootstrap';
import 'jquery-ui';
import 'bootstrap-datepicker';
import 'jquery.resize';
import 'codemirror';
import 'js-yaml';
import 'select2';
import uiRouter from 'angular-ui-router';
// backwards compatibility for $stateChange* events
import 'angular-ui-router/release/stateEvents';


// Configuration dependencies
global.$AnsibleConfig = null;
// Provided via Webpack DefinePlugin in webpack.config.js
global.$ENV = $ENV || null;
// ui-router debugging
if ($ENV['route-debug']){
    let trace = require('angular-ui-router').trace;
    trace.enable();
}

var urlPrefix;

if ($basePath) {
    urlPrefix = $basePath;
}

// Modules
import './helpers';
import './lists';
import './widgets';
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
import managementJobs from './management-jobs/main';
import jobDetail from './job-detail/main';
import workflowResults from './workflow-results/main';
import jobSubmission from './job-submission/main';
import notifications from './notifications/main';
import about from './about/main';
import license from './license/main';
import setupMenu from './setup-menu/main';
import mainMenu from './main-menu/main';
import breadCrumb from './bread-crumb/main';
import browserData from './browser-data/main';
import configuration from './configuration/main';
import dashboard from './dashboard/main';
import moment from './shared/moment/main';
import login from './login/main';
import activityStream from './activity-stream/main';
import standardOut from './standard-out/main';
import Templates from './templates/main';
import credentials from './credentials/main';
import { ProjectsList, ProjectsAdd, ProjectsEdit } from './controllers/Projects';
import { UsersList, UsersAdd, UsersEdit } from './controllers/Users';
import { TeamsList, TeamsAdd, TeamsEdit } from './controllers/Teams';

import RestServices from './rest/main';
import access from './access/main';
import './shared/Modal';
import './shared/prompt-dialog';
import './shared/directives';
import './shared/filters';
import './shared/features/main';
import config from './shared/config/main';
import './login/authenticationServices/pendo/ng-pendo';
import footer from './footer/main';
import scheduler from './scheduler/main';
import { N_ } from './i18n';

var tower = angular.module('Tower', [
    // how to add CommonJS / AMD  third-party dependencies:
    // 1. npm install --save package-name
    // 2. add package name to ./grunt-tasks/webpack.vendorFiles
    require('angular-breadcrumb'),
    require('angular-codemirror'),
    require('angular-drag-and-drop-lists'),
    require('angular-sanitize'),
    require('angular-scheduler').name,
    require('angular-tz-extensions'),
    require('lr-infinite-scroll'),
    require('ng-toast'),
    uiRouter,
    'ui.router.state.events',

    about.name,
    access.name,
    license.name,
    RestServices.name,
    browserData.name,
    configuration.name,
    systemTracking.name,
    inventories.name,
    inventoryScripts.name,
    organizations.name,
    //permissions.name,
    managementJobs.name,
    setupMenu.name,
    mainMenu.name,
    breadCrumb.name,
    dashboard.name,
    moment.name,
    login.name,
    activityStream.name,
    footer.name,
    jobDetail.name,
    workflowResults.name,
    jobSubmission.name,
    notifications.name,
    standardOut.name,
    Templates.name,
    portalMode.name,
    config.name,
    credentials.name,
    //'templates',
    'Utilities',
    'OrganizationFormDefinition',
    'UserFormDefinition',
    'OrganizationListDefinition',
    'templates',
    'UserListDefinition',
    'UserHelper',
    'PromptDialog',
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
    'TemplatesListDefinition',
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
    'lrInfiniteScroll',
    'LoadConfigHelper',
    'PortalJobsListDefinition',
    'features',
    'longDateFilter',
    'pendolytics',
    scheduler.name,
    'ApiModelHelper',
    'ActivityStreamHelper',
    'gettext',
    'I18N',
    'WorkflowFormDefinition',
    'InventorySourcesListDefinition',
    'WorkflowMakerFormDefinition'
])

.constant('AngularScheduler.partials', urlPrefix + 'lib/angular-scheduler/lib/')
    .constant('AngularScheduler.useTimezone', true)
    .constant('AngularScheduler.showUTCField', true)
    .constant('$timezones.definitions.location', urlPrefix + 'lib/angular-tz-extensions/tz/data')
    .config(['$logProvider', function($logProvider) {
        $logProvider.debugEnabled($ENV['ng-debug'] || false);
    }])
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
    .config(['$urlRouterProvider', '$breadcrumbProvider', 'QuerySetProvider',
        '$urlMatcherFactoryProvider', 'stateDefinitionsProvider', '$stateProvider',
        function($urlRouterProvider, $breadcrumbProvider, QuerySet,
            $urlMatcherFactoryProvider, stateDefinitionsProvider, $stateProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();
            $urlMatcherFactoryProvider.strictMode(false);
            $breadcrumbProvider.setOptions({
                templateUrl: urlPrefix + 'partials/breadcrumb.html'
            });

            // route to the details pane of /job/:id/host-event/:eventId if no other child specified
            $urlRouterProvider.when('/jobs/*/host-event/*', '/jobs/*/host-event/*/details');
            $urlRouterProvider.otherwise('/home');

            $urlMatcherFactoryProvider.type('queryset', {
                // encoding
                // from {operator__key1__comparator=value, ... }
                // to "_search=operator:key:compator=value& ... "
                encode: function(item) {
                    return QuerySet.$get().encodeArr(item);
                },
                // decoding
                // from "_search=operator:key:compator=value& ... "
                // to "_search=operator:key:compator=value& ... "
                decode: function(item) {
                    return QuerySet.$get().decodeArr(item);
                },
                // directionality - are we encoding or decoding?
                is: function(item) {
                    // true: encode to uri
                    // false: decode to $stateParam
                    return angular.isObject(item);
                }
            });


            // Handy hook for debugging register/deregister of lazyLoad'd states
            // $stateProvider.stateRegistry.onStatesChanged((event, states) =>{
            //     console.log(event, states)
            // })


            // lazily generate a tree of substates which will replace this node in ui-router's stateRegistry
            // see: stateDefinition.factory for usage documentation
            $stateProvider.state({
                name: 'projects',
                url: '/projects',
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'projects', // top-most node in the generated tree (will replace this state definition)
                    modes: ['add', 'edit'],
                    list: 'ProjectList',
                    form: 'ProjectsForm',
                    controllers: {
                        list: ProjectsList, // DI strings or objects
                        add: ProjectsAdd,
                        edit: ProjectsEdit
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'project',
                        socket: {
                            "groups": {
                                "jobs": ["status_changed"]
                            }
                        }
                    }
                })
            });

            $stateProvider.state({
                name: 'credentials',
                url: '/credentials',
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'credentials',
                    modes: ['add', 'edit'],
                    list: 'CredentialList',
                    form: 'CredentialForm',
                    controllers: {
                        list: CredentialsList,
                        add: CredentialsAdd,
                        edit: CredentialsEdit
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'credential'
                    },
                    ncyBreadcrumb: {
                        parent: 'setup',
                        label: 'CREDENTIALS'
                    }
                })
            });

            $stateProvider.state({
                name: 'teams',
                url: '/teams',
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'teams',
                    modes: ['add', 'edit'],
                    list: 'TeamList',
                    form: 'TeamForm',
                    controllers: {
                        list: TeamsList,
                        add: TeamsAdd,
                        edit: TeamsEdit
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'team'
                    },
                    ncyBreadcrumb: {
                        parent: 'setup',
                        label: 'TEAMS'
                    }
                })
            });

            $stateProvider.state({
                name: 'users',
                url: '/users',
                lazyLoad: () => stateDefinitions.generateTree({
                    parent: 'users',
                    modes: ['add', 'edit'],
                    list: 'UserList',
                    form: 'UserForm',
                    controllers: {
                        list: UsersList,
                        add: UsersAdd,
                        edit: UsersEdit
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'user'
                    },
                    ncyBreadcrumb: {
                        parent: 'setup',
                        label: 'USERS'
                    }
                })
            });
        }
    ])
    .run(['$stateExtender', '$q', '$compile', '$cookieStore', '$rootScope', '$log', '$stateParams',
        'CheckLicense', '$location', 'Authorization', 'LoadBasePaths', 'Timer',
        'ClearScope', 'LoadConfig', 'Store', 'pendoService', 'Prompt', 'Rest',
        'Wait', 'ProcessErrors', '$state', 'GetBasePath', 'ConfigService',
        'FeaturesService', '$filter', 'SocketService', 'I18NInit',
        function($stateExtender, $q, $compile, $cookieStore, $rootScope, $log, $stateParams,
            CheckLicense, $location, Authorization, LoadBasePaths, Timer,
            ClearScope, LoadConfig, Store, pendoService, Prompt, Rest, Wait,
            ProcessErrors, $state, GetBasePath, ConfigService, FeaturesService,
            $filter, SocketService, I18NInit) {

            $rootScope.$state = $state;
            $rootScope.$state.matches = function(stateName) {
                return $state.current.name.search(stateName) > 0;
            };
            $rootScope.$stateParams = $stateParams;

            I18NInit();
            $stateExtender.addState({
                name: 'dashboard',
                url: '/home',
                templateUrl: urlPrefix + 'partials/home.html',
                controller: Home,
                params: { licenseMissing: null },
                data: {
                    activityStream: true,
                    refreshButton: true,
                    socket: {
                        "groups": {
                            "jobs": ["status_changed"]
                        }
                    },
                },
                ncyBreadcrumb: {
                    label: N_("DASHBOARD")
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
            });

            $stateExtender.addState({
                searchPrefix: 'job',
                name: 'jobs',
                url: '/jobs',
                ncyBreadcrumb: {
                    label: N_("JOBS")
                },
                params: {
                    job_search: {
                        value: { order_by: '-finished' }
                    }
                },
                data: {
                    socket: {
                        "groups": {
                            "jobs": ["status_changed"],
                            "schedules": ["changed"]
                        }
                    }
                },
                resolve: {
                    Dataset: ['AllJobsList', 'QuerySet', '$stateParams', 'GetBasePath', (list, qs, $stateParams, GetBasePath) => {
                        let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                        return qs.search(path, $stateParams[`${list.iterator}_search`]);
                    }]
                },
                views: {
                    '@': {
                        templateUrl: urlPrefix + 'partials/jobs.html',
                    },
                    'list@jobs': {
                        templateProvider: function(AllJobsList, generateList) {
                            let html = generateList.build({
                                list: AllJobsList,
                                mode: 'edit'
                            });
                            return html;
                        },
                        controller: JobsListController
                    }
                }
            });


            $stateExtender.addState({
                name: 'teamUsers',
                url: '/teams/:team_id/users',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: UsersList,
                resolve: {
                    Users: ['UsersList', 'QuerySet', '$stateParams', 'GetBasePath', (list, qs, $stateParams, GetBasePath) => {
                        let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                        return qs.search(path, $stateParams[`${list.iterator}_search`]);
                    }]
                }
            });


            $stateExtender.addState({
                name: 'userCredentials',
                url: '/users/:user_id/credentials',
                templateUrl: urlPrefix + 'partials/users.html',
                controller: CredentialsList
            });

            $stateExtender.addState({
                name: 'userCredentialAdd',
                url: '/users/:user_id/credentials/add',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsAdd
            });

            $stateExtender.addState({
                name: 'teamUserCredentialEdit',
                url: '/teams/:user_id/credentials/:credential_id',
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsEdit
            });

            $stateExtender.addState({
                name: 'sockets',
                url: '/sockets',
                templateUrl: urlPrefix + 'partials/sockets.html',
                controller: SocketsController,
                ncyBreadcrumb: {
                    label: 'SOCKETS'
                }
            });

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
                            $state.go('.', null, { reload: true });
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

                // $rootScope.$on('$stateChangeStart', function(event, toState, toParams, fromState) {
                //     SocketService.subscribe(toState, toParams);
                // });

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
