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
       }])

   .factory('GetBasePath', ['$rootScope', '$cookieStore', 'LoadBasePaths',
   function($rootScope, $cookieStore, LoadBasePaths) {
   return function(set) {
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


     