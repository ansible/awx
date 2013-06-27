/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
*/

angular.module('AccessHelper', ['RestServices', 'Utilities'])  
    .factory('CheckAccess', ['$rootScope', 'Alert', 'Rest', 'GetBasePath','ProcessErrors', 'Alert', 
    function($rootScope, Alert, Rest, GetBasePath, ProcessErrors, Prompt) {
    return function(params) {
       var me = $rootScope.current_user;
       var access = false;
       if (me.is_superuser) {
          access = true;
       }
       else {
          if (me.related.admin_of_organizations) {
             Rest.setUrl(me.related.admin_of_organizations);
             Rest.get()
                 .success( function(data, status, headers, config) {
                     if (data.results.length > 0) {
                        access = true;
                     }
                 })
                 .error( function(data, status, headers, config) {
                     ProcessErrors(scope, data, status, null,
                         { hdr: 'Error!', msg: 'Call to ' + me.related.admin_of_organizations + 
                         ' failed. DELETE returned status: ' + status });
                     });  
          }
       }
       if (!access) {
          Alert('Access Denied', 'You do not have access to this function. Please contact your system administrator.');
       }
       return access;
    }
    }]);