// Configuration dependencies
global.$AnsibleConfig = null;
// Provided via Webpack DefinePlugin in webpack.config.js
global.$ENV = {};

global.$ConfigResponse = {};

var urlPrefix;

if ($basePath) {
    urlPrefix = `${$basePath}`;
}

import start from './app.start';
import inventoriesHosts from './inventories-hosts/main';
import inventoryScripts from './inventory-scripts/main';
import credentials from './credentials/main';
import credentialTypes from './credential-types/main';
import organizations from './organizations/main';
import managementJobs from './management-jobs/main';
import workflowResults from './workflow-results/main';
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
import Templates from './templates/main';
import teams from './teams/main';
import users from './users/main';
import projects from './projects/main';
import RestServices from './rest/main';
import access from './access/main';
import scheduler from './scheduler/main';
import instanceGroups from './instance-groups/main';
import shared from './shared/main';

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
        'dndLists',
        'ncy-angular-breadcrumb',
        'ngSanitize',
        'ngCookies',
        'ngToast',
        'gettext',
        'Timezones',
        'lrInfiniteScroll',
        shared.name,
        about.name,
        access.name,
        license.name,
        RestServices.name,
        browserData.name,
        configuration.name,
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
        jobSubmission.name,
        notifications.name,
        Templates.name,
        teams.name,
        users.name,
        projects.name,
        scheduler.name,

        'Utilities',
        'templates',
        'PromptDialog',
        'AWDirectives',

        instanceGroups,
        atFeatures,
        atLibComponents,
        atLibModels,
        atLibServices
    ])
    .constant('AngularScheduler.partials', urlPrefix + 'lib/angular-scheduler/lib/')
    .constant('AngularScheduler.useTimezone', true)
    .constant('AngularScheduler.showUTCField', true)
    .constant('$timezones.definitions.location', urlPrefix + 'lib/angular-tz-extensions/tz/data')
    .config(['$locationProvider', function($locationProvider) {
        $locationProvider.hashPrefix('');
    }])
    .config(['$logProvider', function($logProvider) {
        window.debug = function(){
            $logProvider.debugEnabled(!$logProvider.debugEnabled());
            return $logProvider.debugEnabled();
        };
        window.debug(false);
    }])
    .config(['ngToastProvider', function(ngToastProvider) {
        ngToastProvider.configure({
            animation: 'slide',
            dismissOnTimeout: false,
            dismissButton: true,
            timeout: 4000
        });
    }])
    .config(['$breadcrumbProvider', 'QuerySetProvider',
        '$urlServiceProvider',
        function($breadcrumbProvider, QuerySet,
            $urlServiceProvider) {
            $urlServiceProvider.config.strictMode(false);
            $breadcrumbProvider.setOptions({
                templateUrl: urlPrefix + 'partials/breadcrumb.html'
            });

            // route to the details pane of /job/:id/host-event/:eventId if no other child specified
            $urlServiceProvider.rules.when('/jobs/*/host-event/*', '/jobs/*/host-event/*/details');
            $urlServiceProvider.rules.otherwise('/home');

            $urlServiceProvider.config.type('queryset', {
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
    .run(['$q', '$cookies', '$rootScope', '$log', '$stateParams',
        'CheckLicense', '$location', 'Authorization', 'LoadBasePaths', 'Timer',
        'LoadConfig', 'Store', 'pendoService', 'Rest',
        '$state', 'GetBasePath', 'ConfigService', 'ProcessErrors',
        'SocketService', 'AppStrings', '$transitions', 'i18n',
        function($q, $cookies, $rootScope, $log, $stateParams,
            CheckLicense, $location, Authorization, LoadBasePaths, Timer,
            LoadConfig, Store, pendoService, Rest,
            $state, GetBasePath, ConfigService, ProcessErrors,
            SocketService, AppStrings, $transitions, i18n) {

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
            $rootScope.appStrings = AppStrings;
            $rootScope.$watch('$state.current.ncyBreadcrumbLabel', function(title) {
                title = (title) ? "| " + title : "";
                document.title = `Ansible ${$rootScope.BRAND_NAME} ${title}`;
            });

            $rootScope.$on('ws-approval', () => {
                fetchApprovalsCount();
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

            function fetchApprovalsCount() {
                Rest.setUrl(`${GetBasePath('workflow_approvals')}?status=pending&page_size=1`);
                Rest.get()
                    .then(({data}) => {
                        $rootScope.pendingApprovalCount = data.count;
                    })
                    .catch(({data, status}) => {
                        ProcessErrors({}, data, status, null, {
                            hdr: i18n._('Error!'),
                            msg: i18n._('Failed to get workflow jobs pending approval. GET returned status: ') + status
                        });
                    });
            }

            if ($rootScope.removeConfigReady) {
                $rootScope.removeConfigReady();
            }
            $rootScope.removeConfigReady = $rootScope.$on('ConfigReady', function(evt) {
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

                $transitions.onStart({}, function(trans) {
                    $rootScope.flashMessage = null;

                    $('#form-modal2 .modal-body').empty();

                    $('.tooltip').each(function() {
                        $(this).remove();
                    });

                    $('.popover').each(function() {
                        $(this).remove();
                    });

                    if (trans.to().name !== "templates.editWorkflowJobTemplate.workflowMaker" &&
                        trans.to().name !== "templates.editWorkflowJobTemplate.workflowMaker.inventory" &&
                        trans.to().name !== "templates.editWorkflowJobTemplate.workflowMaker.credential") {
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
                        if (trans.to().name !== "signIn") {
                            $state.go('signIn');
                        }
                    } else if ($rootScope && $rootScope.sessionTimer && $rootScope.sessionTimer.isExpired()) {
                      // gets here on timeout
                        if (trans.to().name !== "signIn") {
                            $state.go('signIn');
                        }
                    } else {
                        if ($rootScope.current_user === undefined || $rootScope.current_user === null) {
                            Authorization.restoreUserInfo(); //user must have hit browser refresh
                        }
                        if (trans.to().name && (trans.to().name !== "signIn"  && trans.to().name !== "signOut" && trans.to().name !== "license")) {
                            ConfigService.getConfig().then(function() {
                                // if not headed to /login or /logout, then check the license
                                CheckLicense.test(evt);
                            });
                        }
                    }
                    activateTab();
                });

                $transitions.onSuccess({}, function(trans) {
                    if(trans.to() === trans.from()) {
                        // check to see if something other than a search param has changed
                        let toParamsWithoutSearchKeys = {};
                        let fromParamsWithoutSearchKeys = {};
                        for (let key in trans.params('to')) {
                            if (trans.params('to').hasOwnProperty(key) && !/_search/.test(key)) {
                                toParamsWithoutSearchKeys[key] = trans.params('to')[key];
                            }
                        }
                        for (let key in trans.params('from')) {
                            if (trans.params('from').hasOwnProperty(key) && !/_search/.test(key)) {
                                fromParamsWithoutSearchKeys[key] = trans.params('from')[key];
                            }
                        }

                        if(!_.isEqual(toParamsWithoutSearchKeys, fromParamsWithoutSearchKeys)) {
                            document.body.scrollTop = document.documentElement.scrollTop = 0;
                        }
                    }
                    else {
                        document.body.scrollTop = document.documentElement.scrollTop = 0;
                    }

                    if (trans.from().name === 'license' && trans.params('to').hasOwnProperty('licenseMissing')) {
                        $rootScope.licenseMissing = trans.params('to').licenseMissing;
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

                    if(_.includes(trans.from().name, 'output') && trans.to().name === 'jobs'){
                        $state.reload();
                    }
                });

                if (!Authorization.isUserLoggedIn()) {
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
                            if (global.$AnsibleConfig.login_redirect_override) {
                                window.location.replace(global.$AnsibleConfig.login_redirect_override);
                            } else {
                                $location.path('/login');
                            }
                        }
                    }
                    // If browser refresh, set the user_is_superuser value
                    $rootScope.user_is_superuser = Authorization.getUserInfo('is_superuser');
                    $rootScope.user_is_system_auditor = Authorization.getUserInfo('is_system_auditor');

                    // state the user refreshes we want to open the socket, except if the user is on the login page, which should happen after the user logs in (see the AuthService module for that call to OpenSocket)
                    if (!_.includes($location.$$url, '/login')) {
                        ConfigService.getConfig().then(function() {
                            Timer.init().then(function(timer) {
                                $rootScope.sessionTimer = timer;
                                SocketService.init();
                                pendoService.issuePendoIdentity();
                                CheckLicense.test();
                                if ($location.$$path === "/home" && $state.current && $state.current.name === "") {
                                    $state.go('dashboard');
                                } else if ($location.$$path === "/portal" && $state.current && $state.current.name === "") {
                                    $state.go('portalMode');
                                }
                            });
                        });
                        fetchApprovalsCount();
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
            if (!$rootScope.basePathsLoaded) {
                // create a promise that will resolve when base paths are loaded
                $rootScope.basePathsLoaded = $q.defer();
            }
            $rootScope.licenseMissing = true;
            //the authorization controller redirects to the home page automatcially if there is no last path defined. in order to override
            // this, set the last path to /portal for instances where portal is visited for the first time.
            $rootScope.lastPath = ($location.path() === "/portal") ? 'portal' : undefined;

            LoadConfig();
        }
    ]);
