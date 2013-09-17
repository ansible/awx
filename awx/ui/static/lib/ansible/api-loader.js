/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  
 *  Read /api and /api/X to discover all the base paths needed
 *  to access the primary model objects.
 *
 */

angular.module('ApiLoader', ['ngCookies'])
   .factory('LoadBasePaths', ['$http', '$rootScope', '$cookieStore', 'ProcessErrors', 
   function($http, $rootScope, $cookieStore, ProcessErrors) {
   return function() {  
       if (!$rootScope['defaultUrls'])
          // if 'defaultUrls', the data used by GetBasePath(), is not in $rootScope, then we need to 
          // restore it from cookieStore or by querying the API.  it goes missing from $rootScope
          // when user hits browser refresh
          if (!$cookieStore.get('api')) {
             // if it's not in cookieStore, then we need to retrieve it from the API
             $http.get('/api/')
                 .success( function(data, status, headers, config) {
                     var base = data.current_version;
                     $http.get(base)
                         .success( function(data, status, headers, config) {
                             data['base'] = base;
                             $rootScope['defaultUrls'] = data;
                             $cookieStore.remove('api');
                             $cookieStore.put('api',data);   //Preserve in cookie to prevent against
                                                             //loss during browser refresh
                             })
                         .error ( function(data, status, headers, config) {
                             $rootScope['defaultUrls'] = { status: 'error' };
                             ProcessErrors(null, data, status, null, 
                                           { hdr: 'Error', msg: 'Failed to read ' + base + '. GET status: ' + status });
                             });      
                     })
                 .error( function(data, status, headers, config) {
                     $rootScope['defaultUrls'] = { status: 'error' };
                     ProcessErrors(null, data, status, null, 
                                   { hdr: 'Error', msg: 'Failed to read /api. GET status: ' + status });
                     });   
          }
          else {
             $rootScope['defaultUrls'] = $cookieStore.get('api');
          }
       }
       }])

   .factory('GetBasePath', ['$rootScope', '$cookieStore', 'LoadBasePaths',
   function($rootScope, $cookieStore, LoadBasePaths) {
   return function(set) {
       // use /api/v1/ results to construct API URLs.
       var answer; 
       if ($rootScope['defaultUrls'] == null || $rootScope['defaultUrls'] == undefined) {
          // browser refresh must have occurred. use what's in session cookie and refresh
          answer = $cookieStore.get('api')[set]; 
          LoadBasePaths(); 
       }
       else {
          answer = $rootScope['defaultUrls'][set];
       }
       return answer;
       }
       }]);


     