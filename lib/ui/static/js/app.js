/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * Our main application mdoule. Declare application routes and perform initialization chores.
 *
 */
angular.module('ansible', [
    'RestServices',
    'AuthService',
    'Utilities',
    'OrganizationFormDefinition', 
    'UserFormDefinition',
    'FormGenerator',
    'OrganizationListDefinition',
    'UserListDefinition', 
    'ListGenerator', 
    'AWToolTip', 
    'PromptDialog',
    'APIDefaults', 
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
    'AWFilters',
    'HostFormDefinition',
    'HostListDefinition',
    'HostHelper',
    'GroupFormDefinition',
    'GroupListDefinition',
    'TeamsListDefinition',
    'TeamFormDefinition',
    'TeamHelper'
     ])
    .config(['$routeProvider', function($routeProvider) {
        $routeProvider.
            when('/inventories', { templateUrl: 'partials/inventories.html',
                                   controller: InventoriesList }).

            when('/inventories/add', { templateUrl: 'partials/inventories.html',
                                       controller: InventoriesAdd }).

            when('/inventories/:id', { templateUrl: 'partials/inventories.html',
                                       controller: InventoriesEdit }).

            when('/inventories/:id/hosts', { templateUrl: 'partials/inventories.html',
                                             controller: HostsList }).

            when('/inventories/:id/hosts/add', { templateUrl: 'partials/inventories.html',
                                                 controller: HostsAdd }).

            when('/inventories/:inventory_id/hosts/:id', { templateUrl: 'partials/inventories.html',
                                                           controller: HostsEdit }).

            when('/inventories/:id/groups', { templateUrl: 'partials/inventories.html',
                                              controller: GroupsList }).

            when('/inventories/:id/groups/add', { templateUrl: 'partials/inventories.html',
                                                  controller: GroupsAdd }).

            when('/inventories/:inventory_id/groups/:id', { templateUrl: 'partials/inventories.html',
                                                             controller: GroupsEdit }).

            when('/organizations', { templateUrl: 'partials/organizations.html',
                                     controller: OrganizationsList }).

            when('/organizations/add', { templateUrl: 'partials/organizations.html',
                                         controller: OrganizationsAdd }).

            when('/organizations/:id', { templateUrl: 'partials/organizations.html',
                                         controller: OrganizationsEdit }).

            when('/organizations/:id/admins', { templateUrl: 'partials/organizations.html',
                                                controller: AdminsList }).

            when('/organizations/:id/users', { templateUrl: 'partials/users.html',
                                               controller: UsersList }).

            when('/organizations/:id/users/add', { templateUrl: 'partials/users.html',
                                                   controller: UsersAdd }).

            when('/organizations/:organization_id/users/:id', { templateUrl: 'partials/users.html',
                                                                controller: UsersEdit }).

            when('/teams', { templateUrl: 'partials/teams.html',
                             controller: TeamsList }).

            when('/teams/add', { templateUrl: 'partials/teams.html',
                                 controller: TeamsAdd }).

            when('/teams/:id', { templateUrl: 'partials/teams.html',
                                 controller: TeamsEdit }).
            
            when('/users', { templateUrl: 'partials/users.html',
                             controller: UsersList }).

            when('/users/add', { templateUrl: 'partials/users.html',
                                 controller: UsersAdd }).

            when('/users/:id', { templateUrl: 'partials/users.html',
                                 controller: UsersEdit }).

            when('/login', { templateUrl: 'partials/login-dialog.html', controller: Authenticate }). 

            when('/logout', { templateUrl: 'partials/login-dialog.html', controller: Authenticate }).
            
            otherwise({redirectTo: '/'});
    }])
    .run(function($rootScope, $location, Authorization) {
        
        $rootScope.breadcrumbs = new Array(); 
        $rootScope.crumbCache = new Array();

        $rootScope.$on("$routeChangeStart", function(event, next, current) {
            // Evaluate the token on each navigation request. Redirect to login page when not valid
            if (Authorization.isTokenValid() == false) {
               if ( next.templateUrl != 'partials/login.html' ) {
                  $location.path('/login');
               }
            }
            else {
               if ($rootScope.current_user == undefined || $rootScope.current_user == null) {
                  Authorization.restoreUserInfo();   //user must have hit browser refresh 
               }
            }
        });

        if (! Authorization.isTokenValid() ) {
           // When the app first loads, redirect to login page
           $location.path('/login');
        }

        // If browser refresh, activate the correct tab
        var base = ($location.path().replace(/^\//,'').split('/')[0]);
        if  (base == '') {
            console.log(base);
            base = 'organizations';
            $location.path('/organizations');
        }
        else {
            $('.nav-tabs a[href="#' + base + '"]').tab('show');
        }     
    });
