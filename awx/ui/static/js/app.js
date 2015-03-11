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
import {Home, HomeGroups, HomeHosts} from 'tower/controllers/Home';
import {SocketsController} from 'tower/controllers/Sockets';
import {Authenticate} from 'tower/controllers/Authentication';
import {CredentialsAdd, CredentialsEdit, CredentialsList} from 'tower/controllers/Credentials';
import {JobsListController} from 'tower/controllers/Jobs';
import {PortalController} from 'tower/controllers/Portal';

import dataServices from 'tower/services/_data-services';
import dashboardGraphs from 'tower/directives/_dashboard-graphs';


import {JobDetailController} from 'tower/controllers/JobDetail';
import {JobStdoutController} from 'tower/controllers/JobStdout';
import {JobTemplatesList, JobTemplatesAdd, JobTemplatesEdit} from 'tower/controllers/JobTemplates';
import {ScheduleEditController} from 'tower/controllers/Schedules';
import {ProjectsList, ProjectsAdd, ProjectsEdit} from 'tower/controllers/Projects';
import {OrganizationsList, OrganizationsAdd, OrganizationsEdit} from 'tower/controllers/Organizations';
import {InventoriesList, InventoriesAdd, InventoriesEdit, InventoriesManage} from 'tower/controllers/Inventories';
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
    'AuthService',
    'Utilities',
    'LicenseHelper',
    'OrganizationFormDefinition',
    'UserFormDefinition',
    'FormGenerator',
    'OrganizationListDefinition',
    'UserListDefinition',
    'UserHelper',
    'ListGenerator',
    'PromptDialog',
    'ApiLoader',
    'RelatedSearchHelper',
    'SearchHelper',
    'PaginationHelpers',
    'RefreshHelper',
    'AdminListDefinition',
    'CustomInventoryListDefinition',
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
    'RunningJobsDefinition',
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
    'QueuedJobsDefinition',
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
    'CustomInventoryListDefinition'
])

    .constant('AngularScheduler.partials', urlPrefix + 'lib/angular-scheduler/lib/')
    .constant('AngularScheduler.useTimezone', true)
    .constant('AngularScheduler.showUTCField', true)
    .constant('$timezones.definitions.location', urlPrefix + 'lib/angular-tz-extensions/tz/data')
    .config(['$routeProvider',
        function ($routeProvider) {

            $routeProvider.

            when('/jobs', {
                templateUrl: urlPrefix + 'partials/jobs.html',
                controller: JobsListController
            }).

            when('/portal', {
                templateUrl: urlPrefix + 'partials/portal.html',
                controller: PortalController
            }).

            when('/jobs/:id', {
                templateUrl: urlPrefix + 'partials/job_detail.html',
                controller: JobDetailController
            }).

            when('/jobs/:id/stdout', {
                templateUrl: urlPrefix + 'partials/job_stdout.html',
                controller: JobStdoutController
            }).

            when('/job_templates', {
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesList
            }).

            when('/job_templates/add', {
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesAdd
            }).

            when('/job_templates/:template_id', {
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: JobTemplatesEdit
            }).

            when('/job_templates/:id/schedules', {
                templateUrl: urlPrefix + 'partials/schedule_detail.html',
                controller: ScheduleEditController
            }).

            when('/projects', {
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsList
            }).

            when('/projects/add', {
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsAdd
            }).

            when('/projects/:id', {
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: ProjectsEdit
            }).

            when('/projects/:id/schedules', {
                templateUrl: urlPrefix + 'partials/schedule_detail.html',
                controller: ScheduleEditController
            }).

            when('/projects/:project_id/organizations', {
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: OrganizationsList
            }).

            when('/projects/:project_id/organizations/add', {
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: OrganizationsAdd
            }).

            when('/inventories', {
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: InventoriesList
            }).

            when('/inventories/add', {
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: InventoriesAdd
            }).

            when('/inventories/:inventory_id', {
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: InventoriesEdit
            }).

            when('/inventories/:inventory_id/manage', {
                templateUrl: urlPrefix + 'partials/inventory-manage.html',
                controller: InventoriesManage
            }).

            when('/organizations', {
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: OrganizationsList
            }).

            when('/organizations/add', {
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: OrganizationsAdd
            }).

            when('/organizations/:organization_id', {
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: OrganizationsEdit
            }).

            when('/organizations/:organization_id/admins', {
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: AdminsList
            }).

            when('/organizations/:organization_id/users', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersList
            }).

            when('/organizations/:organization_id/users/add', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersAdd
            }).

            when('/organizations/:organization_id/users/:user_id', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersEdit
            }).

            when('/teams', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsList
            }).

            when('/teams/add', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsAdd
            }).

            when('/teams/:team_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: TeamsEdit
            }).

            when('/teams/:team_id/permissions/add', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: PermissionsAdd
            }).

            when('/teams/:team_id/permissions', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: PermissionsList
            }).

            when('/teams/:team_id/permissions/:permission_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: PermissionsEdit
            }).

            when('/teams/:team_id/users', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: UsersList
            }).

            when('/teams/:team_id/users/:user_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: UsersEdit
            }).

            when('/teams/:team_id/projects', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsList
            }).

            when('/teams/:team_id/projects/add', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsAdd
            }).

            when('/teams/:team_id/projects/:project_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: ProjectsEdit
            }).

            when('/teams/:team_id/credentials', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsList
            }).

            when('/teams/:team_id/credentials/add', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsAdd
            }).

            when('/teams/:team_id/credentials/:credential_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsEdit
            }).

            when('/credentials', {
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsList
            }).

            when('/credentials/add', {
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsAdd
            }).

            when('/credentials/:credential_id', {
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: CredentialsEdit
            }).

            when('/users', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersList
            }).

            when('/users/add', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersAdd
            }).

            when('/users/:user_id', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: UsersEdit
            }).

            when('/users/:user_id/credentials', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: CredentialsList
            }).

            when('/users/:user_id/permissions/add', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: PermissionsAdd
            }).

            when('/users/:user_id/permissions', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: PermissionsList
            }).

            when('/users/:user_id/permissions/:permission_id', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: PermissionsEdit
            }).

            when('/users/:user_id/credentials/add', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsAdd
            }).

            when('/teams/:user_id/credentials/:credential_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: CredentialsEdit
            }).

            when('/login', {
                templateUrl: urlPrefix + 'partials/blank.html',
                controller: Authenticate
            }).

            when('/logout', {
                templateUrl: urlPrefix + 'partials/blank.html',
                controller: Authenticate
            }).

            when('/home', {
                templateUrl: urlPrefix + 'partials/home.html',
                controller: Home,
                resolve: {
                    graphData: ['$q', 'jobStatusGraphData', 'hostCountGraphData', function($q, jobStatusGraphData, hostCountGraphData) {
                        return $q.all({
                            jobStatus: jobStatusGraphData.get("month", "all"),
                            hostCounts: hostCountGraphData.get()
                        });
                    }]
                }
            }).

            when('/home/groups', {
                templateUrl: urlPrefix + 'partials/subhome.html',
                controller: HomeGroups
            }).

            when('/home/hosts', {
                templateUrl: urlPrefix + 'partials/subhome.html',
                controller: HomeHosts
            }).

            when('/sockets', {
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
        'LoadConfig', 'Store', 'ShowSocketHelp', 'LicenseViewer', 'AboutAnsibleHelp', 'ConfigureTower', 'CreateCustomInventory',
        function ($compile, $cookieStore, $rootScope, $log, CheckLicense, $location, Authorization, LoadBasePaths, Timer, ClearScope, HideStream, Socket,
        LoadConfig, Store, ShowSocketHelp, LicenseViewer, AboutAnsibleHelp, ConfigureTower, CreateCustomInventory) {


            var e, html, sock, checkCount = 0;

            function detectBrowser() {
                var ua = window.navigator.userAgent,
                    browser;
                if (ua.search("MSIE") >= 0) {
                    browser = "MSIE";
                }
                else if (navigator.userAgent.search("Chrome") >= 0 && navigator.userAgent.search("OPR") < 0) {
                    browser = "CHROME";
                }
                else if (navigator.userAgent.search("Firefox") >= 0) {
                    browser = "FF";
                }
                else if (navigator.userAgent.search("Safari") >= 0 && navigator.userAgent.search("Chrome") < 0 && navigator.userAgent.search("OPR") < 0) {
                    browser = "SAFARI";
                }
                else if (navigator.userAgent.search("OPR") >= 0) {
                    browser = "OPERA";
                }
                return browser;
            }

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

                $rootScope.browser = detectBrowser();

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
                        sock = Socket({ scope: $rootScope, endpoint: "jobs" });
                        sock.init();
                        sock.on("status_changed", function(data) {
                            $log.debug('Job ' + data.unified_job_id + ' status changed to ' + data.status);
                            $rootScope.$emit('JobStatusChange', data);
                        });
                        sock.on("summary_complete", function(data) {
                            $log.debug('Job summary_complete ' + data.unified_job_id);
                            $rootScope.$emit('JobSummaryComplete', data);
                        });
                    }
                    openSocket();

                    setTimeout(function() {
                        $rootScope.$apply(function() {
                            sock.checkStatus();
                            $log.debug('socket status: ' + $rootScope.socketStatus);
                        });
                    },2000);

                    // monitor socket status
                    checkCount = 0;
                    $rootScope.dashboardInterval = setInterval(function() {
                        if (sock.checkStatus() === 'error' || checkCount > 5) {
                            // there's an error or we're stuck in a 'connecting' state. attempt to reconnect
                            $log.debug('socket status: ' + sock.checkStatus());
                            $log.debug('attempting new socket connection');
                            sock = null;
                            openSocket();
                            checkCount = 0;
                        }
                        else if (sock.checkStatus() === 'connecting') {
                            checkCount++;
                        }
                        else {
                            checkCount = 0;
                        }
                    }, 5000);
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
                    if ($rootScope.checkSocketConnectionInterval) {
                        // use to monitor and restart socket connections
                        window.clearInterval($rootScope.checkSocketConnectionInterval);
                    }

                    // On each navigation request, check that the user is logged in
                    if (!/^\/(login|logout)/.test($location.path())) {
                        // capture most recent URL, excluding login/logout
                        $rootScope.lastPath = $location.path();
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
                            if($rootScope.dashboardInterval){
                              window.clearInterval($rootScope.dashboardInterval);
                            }
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
                    LicenseViewer.showViewer();
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

                // html = "<a href=\"\" ng-click=\"socketHelp()\" aw-pop-over=\"{{ socketTip }}\" aw-pop-over-watch=\"socketTip\" data-placement=\"bottom\" data-trigger=\"hover\" " +
                //     "data-popover-title=\"Live Events\" data-container=\"body\" style=\"font-size: 10px;\"><i class=\"fa icon-socket-{{ socketStatus }}\"></i></a>";
                // e = angular.element(document.getElementById('socket-beacon-div'));
                // e.empty().append(html);
                // $compile(e)($rootScope);

                // e = angular.element(document.getElementById('socket-beacon-li'));
                // e.empty().append(html);
                // $compile(e)($rootScope);

                // // Listen for job changes and issue callbacks to initiate
                // // DOM updates
                // function openSocket() {
                //     sock = Socket({ scope: $rootScope, endpoint: "jobs" });
                //     sock.init();
                //     sock.on("status_changed", function(data) {
                //         $log.debug('Job ' + data.unified_job_id + ' status changed to ' + data.status);
                //         $rootScope.$emit('JobStatusChange', data);
                //     });
                //     sock.on("summary_complete", function(data) {
                //         $log.debug('Job summary_complete ' + data.unified_job_id);
                //         $rootScope.$emit('JobSummaryComplete', data);
                //     });
                //     sock.on("schedule_change", function(data) {
                //         $log.debug('schedule changed to ' + data.status);
                //         $rootScope.$emit('ScheduleChange', data);
                //     });
                // }

                // if ($rootScope.removeOpenSocket) {
                //     $rootScope.removeOpenSocket();
                // }
                // $rootScope.removeOpenSocket = $rootScope.$on('OpenSocket', function() {

                //     openSocket();

                //     setTimeout(function() {
                //         $rootScope.$apply(function() {
                //             sock.checkStatus();
                //             $log.debug('socket status: ' + $rootScope.socketStatus);
                //         });
                //     },2000);

                //     // monitor socket status
                //     checkCount = 0;
                //     setInterval(function() {
                //         if (sock.checkStatus() === 'error' || checkCount > 5) {
                //             // there's an error or we're stuck in a 'connecting' state. attempt to reconnect
                //             $log.debug('socket status: ' + sock.checkStatus());
                //             $log.debug('attempting new socket connection');
                //             sock = null;
                //             openSocket();
                //             checkCount = 0;
                //         }
                //         else if (sock.checkStatus() === 'connecting') {
                //             checkCount++;
                //         }
                //         else {
                //             checkCount = 0;
                //         }
                //     }, 5000);
                // });

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
