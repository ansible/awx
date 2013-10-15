/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * Our main application mdoule. Declare application routes and perform initialization chores.
 *
 */
 
var urlPrefix = '/static/';

angular.module('ansible', [
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
    'RelatedPaginateHelper',
    'SearchHelper',
    'PaginateHelper',
    'RefreshHelper',
    'AdminListDefinition',
    'AWDirectives',
    'InventoriesListDefinition',
    'InventoryFormDefinition',
    'InventoryHelper',
    'InventoryHostsFormDefinition',
    'InventoryGroupsFormDefinition',
    'InventorySummaryDefinition',
    'AWFilters',
    'HostFormDefinition',
    'HostListDefinition',
    'GroupFormDefinition',
    'GroupListDefinition',
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
    'JobsListDefinition',
    'JobFormDefinition',
    'JobEventsListDefinition',
    'JobEventDataDefinition',
    'JobHostDefinition',
    'GroupsHelper',
    'HostsHelper',
    'ParseHelper',
    'ChildrenHelper',
    'EventsHelper',
    'ProjectPathHelper',
    'md5Helper',
    'AccessHelper',
    'SelectionHelper',
    'LicenseFormDefinition',
    'License',
    'HostGroupsFormDefinition',
    'JobStatusWidget',
    'InventorySyncStatusWidget',
    'SCMSyncStatusWidget',
    'ObjectCountWidget',
    'JobsHelper',
    'InventoryStatusDefinition',
    'InventorySummaryHelpDefinition',
    'InventoryHostsHelpDefinition'
     ])
    .config(['$routeProvider', function($routeProvider) {
        $routeProvider.
            when('/jobs',
                { templateUrl: urlPrefix + 'partials/jobs.html', controller: JobsListCtrl }).

            when('/jobs/:id',
                { templateUrl: urlPrefix + 'partials/jobs.html', controller: JobsEdit }).

            when('/jobs/:id/job_events',
                { templateUrl: urlPrefix + 'partials/jobs.html', controller: JobEventsList }).

            when('/jobs/:id/job_host_summaries',
                { templateUrl: urlPrefix + 'partials/jobs.html', controller: JobHostSummaryList }).
            
            when('/jobs/:job_id/job_events/:event_id',
                { templateUrl: urlPrefix + 'partials/jobs.html', controller: JobEventsEdit }).

            when('/job_templates',
                { templateUrl: urlPrefix + 'partials/job_templates.html', controller: JobTemplatesList }).
            
            when('/job_templates/add',
                { templateUrl: urlPrefix + 'partials/job_templates.html', controller: JobTemplatesAdd }).

            when('/job_templates/:id', 
                { templateUrl: urlPrefix + 'partials/job_templates.html', controller: JobTemplatesEdit }).

            when('/projects', 
                { templateUrl: urlPrefix + 'partials/projects.html', controller: ProjectsList }).

            when('/projects/add', 
                { templateUrl: urlPrefix + 'partials/projects.html', controller: ProjectsAdd }).

            when('/projects/:id', 
                { templateUrl: urlPrefix + 'partials/projects.html', controller: ProjectsEdit }).

            when('/projects/:project_id/organizations',
                { templateUrl: urlPrefix + 'partials/projects.html', controller: OrganizationsList }).

            when('/projects/:project_id/organizations/add',
                { templateUrl: urlPrefix + 'partials/projects.html', controller: OrganizationsAdd }).

            when('/hosts/:id/job_host_summaries', 
                { templateUrl: urlPrefix + 'partials/jobs.html', controller: JobHostSummaryList  }).

            when('/inventories', 
                { templateUrl: urlPrefix + 'partials/inventories.html', controller: InventoriesList }).

            when('/inventories/add', 
                { templateUrl: urlPrefix + 'partials/inventories.html', controller: InventoriesAdd }).

            when('/inventories/:id', 
                { templateUrl: urlPrefix + 'partials/inventories.html', controller: InventoriesEdit }).

            when('/inventories/:inventory_id/hosts', 
                { templateUrl: urlPrefix + 'partials/inventories.html', controller: InventoryHosts }).

            when('/inventories/:inventory_id/groups', 
                { templateUrl: urlPrefix + 'partials/inventories.html', controller: InventoryGroups }).

            when('/organizations', { templateUrl: urlPrefix + 'partials/organizations.html',
                                     controller: OrganizationsList }).

            when('/organizations/add', { templateUrl: urlPrefix + 'partials/organizations.html',
                                         controller: OrganizationsAdd }).

            when('/organizations/:organization_id', { templateUrl: urlPrefix + 'partials/organizations.html',
                                                      controller: OrganizationsEdit }).

            when('/organizations/:organization_id/admins', { templateUrl: urlPrefix + 'partials/organizations.html',
                                                controller: AdminsList }).

            when('/organizations/:organization_id/users', { templateUrl: urlPrefix + 'partials/users.html',
                                                            controller: UsersList }).

            when('/organizations/:organization_id/users/add', { templateUrl: urlPrefix + 'partials/users.html',
                                                                controller: UsersAdd }).

            when('/organizations/:organization_id/users/:user_id', { templateUrl: urlPrefix + 'partials/users.html',
                                                                     controller: UsersEdit }).

            when('/teams', { templateUrl: urlPrefix + 'partials/teams.html',
                             controller: TeamsList }).

            when('/teams/add', { templateUrl: urlPrefix + 'partials/teams.html',
                                 controller: TeamsAdd }).

            when('/teams/:team_id', { templateUrl: urlPrefix + 'partials/teams.html',
                                      controller: TeamsEdit }).
            
            when('/teams/:team_id/permissions/add', { templateUrl: urlPrefix + 'partials/teams.html',
                                                      controller: PermissionsAdd }).

            when('/teams/:team_id/permissions', { templateUrl: urlPrefix + 'partials/teams.html',
                                                  controller: PermissionsList }).

            when('/teams/:team_id/permissions/:permission_id', { templateUrl: urlPrefix + 'partials/teams.html',
                                                                 controller: PermissionsEdit }).

            when('/teams/:team_id/users', { templateUrl: urlPrefix + 'partials/teams.html',
                                            controller: UsersList }).

            when('/teams/:team_id/users/:user_id', { templateUrl: urlPrefix + 'partials/teams.html',
                                                     controller: UsersEdit }).

            when('/teams/:team_id/projects', { templateUrl: urlPrefix + 'partials/teams.html',
                                               controller: ProjectsList }).

            when('/teams/:team_id/projects/add', { templateUrl: urlPrefix + 'partials/teams.html',
                                                   controller: ProjectsAdd }).

            when('/teams/:team_id/projects/:project_id', { templateUrl: urlPrefix + 'partials/teams.html',
                                                           controller: ProjectsEdit }).
          
            when('/teams/:team_id/credentials', { templateUrl: urlPrefix + 'partials/teams.html',
                                                  controller: CredentialsList }).

            when('/teams/:team_id/credentials/add', { templateUrl: urlPrefix + 'partials/teams.html',
                                                      controller: CredentialsAdd }).

            when('/teams/:team_id/credentials/:credential_id', { templateUrl: urlPrefix + 'partials/teams.html',
                                                                 controller: CredentialsEdit }).

            when('/credentials', { templateUrl: urlPrefix + 'partials/credentials.html',
                                   controller: CredentialsList }).

            when('/credentials/:credential_id', { templateUrl: urlPrefix + 'partials/credentials.html',
                                                  controller: CredentialsEdit }).
            
            when('/users', { templateUrl: urlPrefix + 'partials/users.html',
                             controller: UsersList }).

            when('/users/add', { templateUrl: urlPrefix + 'partials/users.html',
                                 controller: UsersAdd }).

            when('/users/:user_id', { templateUrl: urlPrefix + 'partials/users.html',
                                      controller: UsersEdit }).

            when('/users/:user_id/credentials', { templateUrl: urlPrefix + 'partials/users.html',
                                                  controller: CredentialsList }).

            when('/users/:user_id/permissions/add', { templateUrl: urlPrefix + 'partials/users.html',
                                                      controller: PermissionsAdd }).

            when('/users/:user_id/permissions', { templateUrl: urlPrefix + 'partials/users.html',
                                                  controller: PermissionsList }).

            when('/users/:user_id/permissions/:permission_id', { templateUrl: urlPrefix + 'partials/users.html',
                                                                 controller: PermissionsEdit }).

            when('/users/:user_id/credentials/add', { templateUrl: urlPrefix + 'partials/teams.html',
                                                      controller: CredentialsAdd }).

            when('/teams/:user_id/credentials/:credential_id', { templateUrl: urlPrefix + 'partials/teams.html',
                                                                 controller: CredentialsEdit }).

            when('/login', { templateUrl: urlPrefix + 'partials/organizations.html', controller: Authenticate }). 

            when('/logout', { templateUrl: urlPrefix + 'partials/organizations.html', controller: Authenticate }).

            when('/home', { templateUrl: urlPrefix + 'partials/home.html', controller: Home }).
            
            otherwise({redirectTo: '/home'});
    }])
    .run(['$cookieStore', '$rootScope', 'CheckLicense', '$location', 'Authorization','LoadBasePaths', 'ViewLicense',
         function($cookieStore, $rootScope, CheckLicense, $location, Authorization, LoadBasePaths, ViewLicense) {
        
        LoadBasePaths();
        
        if ( !(typeof $AnsibleConfig.refresh_rate == 'number' && $AnsibleConfig.refresh_rate >= 3
               && $AnsibleConfig.refresh_rate <= 99) ) {
           $AnsibleConfig.refresh_rate = 10;
        }

        $rootScope.breadcrumbs = new Array(); 
        $rootScope.crumbCache = new Array();
        
        $rootScope.$on("$routeChangeStart", function(event, next, current) {
            // On each navigation request, check that the user is logged in
            if (Authorization.isUserLoggedIn() == false) {
               if ( next.templateUrl != (urlPrefix + 'partials/login.html') ) {
                  $location.path('/login');
               }
            }
            else {
               if ($rootScope.current_user == undefined || $rootScope.current_user == null) {
                  Authorization.restoreUserInfo();   //user must have hit browser refresh 
               }
               CheckLicense();
            }

            if ($rootScope.timer) {
               clearInterval($rootScope.timer);
               $rootScope.timer = null;
            }

            // Make the correct tab active
            var base = $location.path().replace(/^\//,'').split('/')[0];
            if (base == '') {
               base = 'home';
            }
            else {
               base.replace(/\_/g,' ');
            }
            $('.nav-tabs a[href="#' + base + '"]').tab('show');
            });

        if (!Authorization.getToken()) {
           // When the app first loads, redirect to login page
           $rootScope.sessionExpired = false;
           $cookieStore.put('sessionExpired', false);
           $location.path('/login');
        }
        
        // If browser refresh, activate the correct tab
        var base = ($location.path().replace(/^\//,'').split('/')[0]);
        if  (base == '') {
            base = 'home';
            $location.path('/home');
        }
        else {
            base.replace(/\_/g,' ');
        }
        $('.nav-tabs a[href="#' + base + '"]').tab('show');

        $rootScope.viewCurrentUser = function() {
            $location.path('/users/' + $rootScope.current_user.id);
            }

        $rootScope.viewLicense = function() {
            //$location.path('/license');
            ViewLicense();
            }   
    }]);
