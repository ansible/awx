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
global.$ENV = {} ;
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
import './filters';
import portalMode from './portal-mode/main';
import systemTracking from './system-tracking/main';
import inventories from './inventories/main';
import inventoryScripts from './inventory-scripts/main';
import organizations from './organizations/main';
import managementJobs from './management-jobs/main';
import workflowResults from './workflow-results/main';
import jobResults from './job-results/main';
import jobSubmission from './job-submission/main';
import notifications from './notifications/main';
import about from './about/main';
import license from './license/main';
import setupMenu from './setup-menu/main';
import mainMenu from './main-menu/main';
import breadCrumb from './bread-crumb/main';
import browserData from './browser-data/main';
import configuration from './configuration/main';
import home from './home/main';
import moment from './shared/moment/main';
import login from './login/main';
import activityStream from './activity-stream/main';
import standardOut from './standard-out/main';
import Templates from './templates/main';
import credentials from './credentials/main';
import jobs from './jobs/main';
import teams from './teams/main';
import users from './users/main';
import projects from './projects/main';

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
    'gettext',
    'I18N',
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
    home.name,
    moment.name,
    login.name,
    activityStream.name,
    footer.name,
    workflowResults.name,
    jobResults.name,
    jobSubmission.name,
    notifications.name,
    standardOut.name,
    Templates.name,
    portalMode.name,
    config.name,
    credentials.name,
    jobs.name,
    teams.name,
    users.name,
    projects.name,
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
        '$urlMatcherFactoryProvider',
        function($urlRouterProvider, $breadcrumbProvider, QuerySet,
            $urlMatcherFactoryProvider) {
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
                // to {operator__key1__comparator=value, ... }
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
        }
    ])
    .run(['$stateExtender', '$q', '$compile', '$cookieStore', '$rootScope', '$log', '$stateParams',
        'CheckLicense', '$location', 'Authorization', 'LoadBasePaths', 'Timer',
        'ClearScope', 'LoadConfig', 'Store', 'pendoService', 'Prompt', 'Rest',
        'Wait', 'ProcessErrors', '$state', 'GetBasePath', 'ConfigService',
        'FeaturesService', '$filter', 'SocketService',
        function($stateExtender, $q, $compile, $cookieStore, $rootScope, $log, $stateParams,
            CheckLicense, $location, Authorization, LoadBasePaths, Timer,
            ClearScope, LoadConfig, Store, pendoService, Prompt, Rest, Wait,
            ProcessErrors, $state, GetBasePath, ConfigService, FeaturesService,
            $filter, SocketService) {

            $rootScope.$state = $state;
            $rootScope.$state.matches = function(stateName) {
                return $state.current.name.search(stateName) > 0;
            };
            $rootScope.$stateParams = $stateParams;

            $state.defaultErrorHandler(function(error) {
                $log.debug(`$state.defaultErrorHandler: ${error}`);
            });

            $rootScope.refresh = function() {
                $state.go('.', null, {reload: true});
            };

            $rootScope.refreshJobs = function(){
                $state.go('.', null, {reload: true});
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

                $rootScope.$on("$stateChangeStart", function (event, next) {
                    // Remove any lingering intervals
                    // except on jobDetails.* states
                    var jobDetailStates = [
                        'jobDetail',
                        'jobDetail.host-summary',
                        'jobDetail.host-event.details',
                        'jobDetail.host-event.json',
                        'jobDetail.host-events',
                        'jobDetail.host-event.stdout'
                    ];
                    if ($rootScope.jobDetailInterval && !_.includes(jobDetailStates, next.name) ) {
                        window.clearInterval($rootScope.jobDetailInterval);
                    }
                    if ($rootScope.jobStdOutInterval && !_.includes(jobDetailStates, next.name) ) {
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
                        if (next.name !== "signIn") {
                            $state.go('signIn');
                        }
                    } else if ($rootScope && $rootScope.sessionTimer && $rootScope.sessionTimer.isExpired()) {
                      // gets here on timeout
                        if (next.name !== "signIn") {
                            $state.go('signIn');
                        }
                    } else {
                        if ($rootScope.current_user === undefined || $rootScope.current_user === null) {
                            Authorization.restoreUserInfo(); //user must have hit browser refresh
                        }
                        if (next && (next.name !== "signIn"  && next.name !== "signOut" && next.name !== "license")) {
                            if($rootScope.configReady === true){
                                // if not headed to /login or /logout, then check the license
                                CheckLicense.test(event);
                            }

                        }
                    }
                    activateTab();
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
