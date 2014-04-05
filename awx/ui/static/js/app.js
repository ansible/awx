/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * Our main application mdoule. Declare application routes and perform initialization chores.
 *
 */
var urlPrefix = $basePath;

angular.module('ansible', [
    'ngRoute',
    'ngSanitize',
    'ngCookies',
    'RestServices',
    'AuthService',
    'Utilities',
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
    'JobTemplateFormDefinition',
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
    'JobEventsListDefinition',
    'JobEventDataDefinition',
    'JobEventsFormDefinition',
    'JobHostDefinition',
    'JobSummaryDefinition',
    'ParseHelper',
    'ChildrenHelper',
    'EventsHelper',
    'ProjectPathHelper',
    'md5Helper',
    'AccessHelper',
    'SelectionHelper',
    'License',
    'HostGroupsFormDefinition',
    'JobStatusWidget',
    'InventorySyncStatusWidget',
    'SCMSyncStatusWidget',
    'ObjectCountWidget',
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
    'LogViewerOptionsDefinition'
])
    
    .constant('AngularScheduler.partials', $basePath + 'lib/angular-scheduler/lib/')
    .constant('AngularScheduler.useTimezone', true)
    .constant('AngularScheduler.showUTCField', true)
    .constant('$timezones.definitions.location', $basePath + 'lib/angular-tz-extensions/tz/data')

    .config(['$routeProvider',
        function ($routeProvider) {
            $routeProvider.
            when('/jobs', {
                templateUrl: urlPrefix + 'partials/jobs.html',
                controller: 'JobsListController'
            }).
            
            when('/job_events/:id', {
                templateUrl: urlPrefix + 'partials/job_events.html',
                controller: 'JobEventsList'
            }).

            when('/job_host_summaries/:id', {
                templateUrl: urlPrefix + 'partials/job_host_summaries.html',
                controller: 'JobHostSummaryList'
            }).

            when('/jobs/:job_id/job_events/:event_id', {
                templateUrl: urlPrefix + 'partials/jobs.html',
                controller: 'JobEventsEdit'
            }).

            when('/job_templates', {
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: 'JobTemplatesList'
            }).

            when('/job_templates/add', {
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: 'JobTemplatesAdd'
            }).

            when('/job_templates/:template_id', {
                templateUrl: urlPrefix + 'partials/job_templates.html',
                controller: 'JobTemplatesEdit'
            }).

            when('/job_templates/:id/schedules', {
                templateUrl: urlPrefix + 'partials/schedule_detail.html',
                controller: 'ScheduleEditController'
            }).

            when('/projects', {
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: 'ProjectsList'
            }).

            when('/projects/add', {
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: 'ProjectsAdd'
            }).

            when('/projects/:id', {
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: 'ProjectsEdit'
            }).
            
            when('/projects/:id/schedules', {
                templateUrl: urlPrefix + 'partials/schedule_detail.html',
                controller: 'ScheduleEditController'
            }).

            when('/projects/:project_id/organizations', {
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: 'OrganizationsList'
            }).

            when('/projects/:project_id/organizations/add', {
                templateUrl: urlPrefix + 'partials/projects.html',
                controller: 'OrganizationsAdd'
            }).

            when('/hosts/:id/job_host_summaries', {
                templateUrl: urlPrefix + 'partials/jobs.html',
                controller: 'JobHostSummaryList'
            }).

            when('/inventories', {
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: 'InventoriesList'
            }).

            when('/inventories/add', {
                templateUrl: urlPrefix + 'partials/inventories.html',
                controller: 'InventoriesAdd'
            }).

            when('/inventories/:inventory_id', {
                templateUrl: urlPrefix + 'partials/inventory-edit.html',
                controller: 'InventoriesEdit'
            }).

            when('/organizations', {
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: 'OrganizationsList'
            }).

            when('/organizations/add', {
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: 'OrganizationsAdd'
            }).

            when('/organizations/:organization_id', {
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: 'OrganizationsEdit'
            }).

            when('/organizations/:organization_id/admins', {
                templateUrl: urlPrefix + 'partials/organizations.html',
                controller: 'AdminsList'
            }).

            when('/organizations/:organization_id/users', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: 'UsersList'
            }).

            when('/organizations/:organization_id/users/add', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: 'UsersAdd'
            }).

            when('/organizations/:organization_id/users/:user_id', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: 'UsersEdit'
            }).

            when('/teams', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'TeamsList'
            }).

            when('/teams/add', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'TeamsAdd'
            }).

            when('/teams/:team_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'TeamsEdit'
            }).

            when('/teams/:team_id/permissions/add', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'PermissionsAdd'
            }).

            when('/teams/:team_id/permissions', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'PermissionsList'
            }).

            when('/teams/:team_id/permissions/:permission_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'PermissionsEdit'
            }).

            when('/teams/:team_id/users', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'UsersList'
            }).

            when('/teams/:team_id/users/:user_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'UsersEdit'
            }).

            when('/teams/:team_id/projects', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'ProjectsList'
            }).

            when('/teams/:team_id/projects/add', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'ProjectsAdd'
            }).

            when('/teams/:team_id/projects/:project_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'ProjectsEdit'
            }).

            when('/teams/:team_id/credentials', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'CredentialsList'
            }).

            when('/teams/:team_id/credentials/add', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'CredentialsAdd'
            }).

            when('/teams/:team_id/credentials/:credential_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'CredentialsEdit'
            }).

            when('/credentials', {
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: 'CredentialsList'
            }).

            when('/credentials/add', {
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: 'CredentialsAdd'
            }).

            when('/credentials/:credential_id', {
                templateUrl: urlPrefix + 'partials/credentials.html',
                controller: 'CredentialsEdit'
            }).

            when('/users', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: 'UsersList'
            }).

            when('/users/add', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: 'UsersAdd'
            }).

            when('/users/:user_id', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: 'UsersEdit'
            }).

            when('/users/:user_id/credentials', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: 'CredentialsList'
            }).

            when('/users/:user_id/permissions/add', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: 'PermissionsAdd'
            }).

            when('/users/:user_id/permissions', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: 'PermissionsList'
            }).

            when('/users/:user_id/permissions/:permission_id', {
                templateUrl: urlPrefix + 'partials/users.html',
                controller: 'PermissionsEdit'
            }).

            when('/users/:user_id/credentials/add', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'CredentialsAdd'
            }).

            when('/teams/:user_id/credentials/:credential_id', {
                templateUrl: urlPrefix + 'partials/teams.html',
                controller: 'CredentialsEdit'
            }).

            when('/login', {
                templateUrl: urlPrefix + 'partials/home.html',
                controller: 'Authenticate'
            }).

            when('/logout', {
                templateUrl: urlPrefix + 'partials/home.html',
                controller: 'Authenticate'
            }).

            when('/home', {
                templateUrl: urlPrefix + 'partials/home.html',
                controller: 'Home'
            }).

            when('/home/groups', {
                templateUrl: urlPrefix + 'partials/subhome.html',
                controller: 'HomeGroups'
            }).

            when('/home/hosts', {
                templateUrl: urlPrefix + 'partials/subhome.html',
                controller: 'HomeHosts'
            }).

            otherwise({
                redirectTo: '/home'
            });
        }
    ])
    .run(['$cookieStore', '$rootScope', 'CheckLicense', '$location', 'Authorization', 'LoadBasePaths', 'ViewLicense',
        'Timer', 'ClearScope', 'HideStream',
        function ($cookieStore, $rootScope, CheckLicense, $location, Authorization, LoadBasePaths, ViewLicense,
            Timer, ClearScope, HideStream) {

            LoadBasePaths();

            $rootScope.breadcrumbs = [];
            $rootScope.crumbCache = [];
            $rootScope.sessionTimer = Timer.init();

            $rootScope.$on("$routeChangeStart", function (event, next) {

                // Before navigating away from current tab, make sure the primary view is visible
                if ($('#stream-container').is(':visible')) {
                    HideStream();
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
                    if (next.templateUrl !== (urlPrefix + 'partials/login.html')) {
                        $rootScope.sessionTimer.expireSession();
                        $location.path('/login');
                    }
                } else {
                    if ($rootScope.current_user === undefined || $rootScope.current_user === null) {
                        Authorization.restoreUserInfo(); //user must have hit browser refresh 
                    }
                    CheckLicense();
                }

                // Make the correct tab active
                var base = $location.path().replace(/^\//, '').split('/')[0];
                if (base === '') {
                    base = 'home';
                } else {
                    base.replace(/\_/g, ' ');
                    base = (base === 'job_events' || base === 'job_host_summaries') ? 'jobs' : base;
                }
                $('.nav-tabs a[href="#' + base + '"]').tab('show');
            });

            if (!Authorization.getToken()) {
                // When the app first loads, redirect to login page
                $rootScope.sessionExpired = false;
                $cookieStore.put('sessionExpired', false);
                $location.path('/login');
            } else {
                // If browser refresh, set the user_is_superuser value
                $rootScope.user_is_superuser = Authorization.getUserInfo('is_superuser');
            }

            // If browser refresh, activate the correct tab
            var base = ($location.path().replace(/^\//, '').split('/')[0]);
            if (base === '') {
                base = 'home';
                $location.path('/home');
            } else {
                base.replace(/\_/g, ' ');
                if (base === 'jobevents' || base === 'jobhostsummaries') {
                    base = 'jobs';
                }
            }
            $('.nav-tabs a[href="#' + base + '"]').tab('show');

            $rootScope.viewCurrentUser = function () {
                $location.path('/users/' + $rootScope.current_user.id);
            };

            $rootScope.viewLicense = function () {
                ViewLicense();
            };
            $rootScope.toggleTab = function(e, tab, tabs) {
                e.preventDefault();
                $('#' + tabs + ' #' + tab).tab('show');
            };
        }
    ]);