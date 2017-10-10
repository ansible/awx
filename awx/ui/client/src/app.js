// Configuration dependencies
global.$AnsibleConfig = null;
// Provided via Webpack DefinePlugin in webpack.config.js
global.$ENV = {};
// ui-router debugging
if ($ENV['route-debug']){
    let trace = angular.module('ui.router').trace;
    trace.enable();
}

var urlPrefix;

if ($basePath) {
    urlPrefix = `${$basePath}`;
}

import start from './app.start';

import portalMode from './portal-mode/main';
import systemTracking from './system-tracking/main';
import inventoriesHosts from './inventories-hosts/main';
import inventoryScripts from './inventory-scripts/main';
import credentials from './credentials/main';
import credentialTypes from './credential-types/main';
import organizations from './organizations/main';
import managementJobs from './management-jobs/main';
import workflowResults from './workflow-results/main';
import jobResults from './job-results/main';
import jobSubmission from './job-submission/main';
import notifications from './notifications/main';
import about from './about/main';
import license from './license/main';
import breadCrumb from './bread-crumb/main';
import browserData from './browser-data/main';
import configuration from './configuration/main';
import home from './home/main';
import login from './login/main';
import activityStream from './activity-stream/main';
import standardOut from './standard-out/main';
import Templates from './templates/main';
import jobs from './jobs/main';
import teams from './teams/main';
import users from './users/main';
import projects from './projects/main';
import RestServices from './rest/main';
import access from './access/main';
import scheduler from './scheduler/main';
import instanceGroups from './instance-groups/main';

import atFeatures from '~features';
import atLibComponents from '~components';
import atLibModels from '~models';
import atLibServices from '~services';

start.bootstrap(() => {
    angular.bootstrap(document.body, ['awApp']);
});

angular
    .module('awApp', [
        'I18N',
        'AngularCodeMirrorModule',
        'angular-duration-format',
        'angularMoment',
        'AngularScheduler',
        'angular-md5',
        'dndLists',
        'ncy-angular-breadcrumb',
        'ngSanitize',
        'ngCookies',
        'ngToast',
        'gettext',
        'Timezones',
        'ui.router',
        'ui.router.state.events',
        'lrInfiniteScroll',

        about.name,
        access.name,
        license.name,
        RestServices.name,
        browserData.name,
        configuration.name,
        systemTracking.name,
        inventoriesHosts.name,
        inventoryScripts.name,
        credentials.name,
        credentialTypes.name,
        organizations.name,
        managementJobs.name,
        breadCrumb.name,
        home.name,
        login.name,
        activityStream.name,
        workflowResults.name,
        jobResults.name,
        jobSubmission.name,
        notifications.name,
        standardOut.name,
        Templates.name,
        portalMode.name,
        jobs.name,
        teams.name,
        users.name,
        projects.name,
        scheduler.name,
        instanceGroups.name,

        'Utilities',
        'templates',
        'PromptDialog',
        'AWDirectives',
        'features',

        atFeatures,
        atLibComponents,
        atLibModels,
        atLibServices
    ])
    .constant('AngularScheduler.partials', urlPrefix + 'lib/angular-scheduler/lib/')
    .constant('AngularScheduler.useTimezone', true)
    .constant('AngularScheduler.showUTCField', true)
    .constant('$timezones.definitions.location', urlPrefix + 'lib/angular-tz-extensions/tz/data')
    .config(['$logProvider', function($logProvider) {
        $logProvider.debugEnabled($ENV['ng-debug'] || false);
    }])
    .config(['ngToastProvider', function(ngToastProvider) {
        ngToastProvider.configure({
            animation: 'slide',
            dismissOnTimeout: false,
            dismissButton: true,
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
    .run(['$stateExtender', '$q', '$compile', '$cookies', '$rootScope', '$log', '$stateParams',
        'CheckLicense', '$location', 'Authorization', 'LoadBasePaths', 'Timer',
        'LoadConfig', 'Store', 'pendoService', 'Prompt', 'Rest',
        'Wait', 'ProcessErrors', '$state', 'GetBasePath', 'ConfigService',
        'FeaturesService', '$filter', 'SocketService', 'AppStrings',
        function($stateExtender, $q, $compile, $cookies, $rootScope, $log, $stateParams,
            CheckLicense, $location, Authorization, LoadBasePaths, Timer,
            LoadConfig, Store, pendoService, Prompt, Rest, Wait,
            ProcessErrors, $state, GetBasePath, ConfigService, FeaturesService,
            $filter, SocketService, AppStrings) {

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

            $rootScope.breadcrumb = {};
            $rootScope.BRAND_NAME = AppStrings.get('BRAND_NAME');
            $rootScope.tabTitle = `Ansible ${$rootScope.BRAND_NAME}`;
            $rootScope.$watch('$state.current.ncyBreadcrumbLabel', function(title) {
                title = (title) ? "| " + title : "";
                $rootScope.tabTitle = `Ansible ${$rootScope.BRAND_NAME} ${title}`;
            });

            function activateTab() {
                // Make the correct tab active
                var base = $location.path().replace(/^\//, '').split('/')[0];

                if (base === '') {
                    base = 'home';
                } else {
                    //base.replace(/\_/g, ' ');
                    base = (base === 'job_events' || base === 'job_host_summaries') ? 'jobs' : base;
                }
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
                    // let current_title = $rootScope.$state.current.ncyBreadcrumbLabel || "";
                    // $rootScope.tabTitle = `Ansible ${$rootScope.BRAND_NAME} ${current_title}`;
                    // Remove any lingering intervals
                    // except on jobResults.* states
                    var jobResultStates = [
                        'jobResult',
                        'jobResult.host-summary',
                        'jobResult.host-event.details',
                        'jobResult.host-event.json',
                        'jobResult.host-events',
                        'jobResult.host-event.stdout'
                    ];
                    if ($rootScope.jobResultInterval && !_.includes(jobResultStates, next.name) ) {
                        window.clearInterval($rootScope.jobResultInterval);
                    }
                    if ($rootScope.jobStdOutInterval && !_.includes(jobResultStates, next.name) ) {
                        window.clearInterval($rootScope.jobStdOutInterval);
                    }

                    $rootScope.flashMessage = null;

                    $('#form-modal2 .modal-body').empty();

                    $('.tooltip').each(function() {
                        $(this).remove();
                    });

                    $('.popover').each(function() {
                        $(this).remove();
                    });

                    if (next.name !== "templates.editWorkflowJobTemplate.workflowMaker" &&
                        next.name !== "templates.editWorkflowJobTemplate.workflowMaker.inventory" &&
                        next.name !== "templates.editWorkflowJobTemplate.workflowMaker.credential") {
                            $('.ui-dialog-content').each(function() {
                                $(this).dialog('close');
                            });
                    }

                    try {
                        $('#help-modal').dialog('close');
                    } catch (e) {
                        // ignore
                    }

                    // On each navigation request, check that the user is logged in
                    if (!/^\/(login|logout)/.test($location.path())) {
                        // capture most recent URL, excluding login/logout
                        $rootScope.lastPath = $location.path();
                        $rootScope.enteredPath = $location.path();
                        $cookies.put('lastPath', $location.path());
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
                            ConfigService.getConfig().then(function() {
                                // if not headed to /login or /logout, then check the license
                                CheckLicense.test(event);
                            });
                        }
                    }
                    activateTab();
                });

                $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams) {

                    if(toState === fromState) {
                        // check to see if something other than a search param has changed
                        let toParamsWithoutSearchKeys = {};
                        let fromParamsWithoutSearchKeys = {};
                        for (let key in toParams) {
                            if (toParams.hasOwnProperty(key) && !/_search/.test(key)) {
                                toParamsWithoutSearchKeys[key] = toParams[key];
                            }
                        }
                        for (let key in fromParams) {
                            if (fromParams.hasOwnProperty(key) && !/_search/.test(key)) {
                                fromParamsWithoutSearchKeys[key] = fromParams[key];
                            }
                        }

                        if(!_.isEqual(toParamsWithoutSearchKeys, fromParamsWithoutSearchKeys)) {
                            document.body.scrollTop = document.documentElement.scrollTop = 0;
                        }
                    }
                    else {
                        document.body.scrollTop = document.documentElement.scrollTop = 0;
                    }

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
                    if (!/^\/(login|logout)/.test($location.path())) {
                        $rootScope.preAuthUrl = $location.path();
                    }
                    $location.path('/login');
                } else {
                    var lastUser = $cookies.getObject('current_user'),
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
