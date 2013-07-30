/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * User authentication functions
 *
 */

angular.module('AuthService', ['ngCookies', 'OrganizationFormDefinition'])
   .factory('Authorization', ['$http', '$rootScope', '$location', '$cookieStore', 'OrganizationForm', 
   function($http, $rootScope, $location, $cookieStore, OrganizationForm) {
   return {
       setToken: function(token) {
           // set the session cookie
           var today = new Date();
           today.setTime(today.getTime() + ($AnsibleConfig.session_timeout * 1000));
           $cookieStore.remove('token');
           $cookieStore.remove('token_expire');
           $cookieStore.put('token', token);
           $cookieStore.put('token_expire', today.getTime());
           $rootScope.token = token;
           $rootScope.userLoggedIn = true;
           $rootScope.token_expire = today.getTime();
           },

       isTokenValid: function() {
           // check if token exists and is not expired
           var response = false;
           var token = ($rootScope.token) ? $rootScope.token : $cookieStore.get('token'); 
           var token_expire = ($rootScope.token_expire) ? $rootScope.token_expire : $cookieStore.get('token_expire');
           if (token && token_expire) {
              var exp = new Date(token_expire);
              var today = new Date();
              if (today < exp) {
                 this.setToken(token);  //push expiration into the future while user is active
                 response = true;
              }
           }
           return response;
           },

       didSessionExpire: function() {
           // use only to test why user was sent to login page. 
           var response = false;
           var token_expire = ($rootScope.token_expire) ? $rootScope.token_expire : $cookieStore.get('token_expire');
           if (token_expire) {
              var exp = new Date(token_expire);
              var today = new Date();
              if (exp < today) {
                 response = true;
              }
           }
           return response;
       },
       
       getToken: function() {
           if ( this.isTokenValid() ) {
              return ($rootScope.token) ? $rootScope.token : $cookieStore.get('token'); 
           }
           else {
              return null;
           }
       },

       retrieveToken: function(username, password) {
           return $http({ method: 'POST', url: '/api/v1/authtoken/', 
                          data: {"username": username, "password": password} });
           },
       
       logout: function() {
           // the following puts our primary scope up for garbage collection, which
           // should prevent content flash from the prior user.
           var scope = angular.element(document.getElementById('main-view')).scope();
           scope.$destroy();
           $rootScope.$destroy();
           
           // Reset the scope for organizations. No matter what we have tried, nothing seems
           // to clear the scope fast enough to prevent prior user's content from displaying
           $rootScope['organizations'] = null;
           for (var set in OrganizationForm.related) {
               $rootScope[set] = null;
           }
           
           $cookieStore.remove('accordions');
           $cookieStore.remove('token'); 
           $cookieStore.remove('token_expire');
           $cookieStore.remove('current_user');
           $rootScope.current_user = {};
           $rootScope.license_tested = undefined;
           $rootScope.userLoggedIn = false;
           $rootScope.token = null;
           $rootScope.token_expire = new Date(1970, 0, 1, 0, 0, 0, 0);
           },

       getLicense: function() {
           return $http({
               method: 'GET',
               url: '/api/v1/config/',
               headers: { 'Authorization': 'Token ' + this.getToken() }
               });
           },

       setLicense: function(license) {
           license['tested'] = false;
           $cookieStore.put('license', license);
           },

       licenseTested: function() {
           var result;
           if ($rootScope.license_tested !== undefined) {
              result = $rootScope.license_tested;
           }
           else {          
              var license = $cookieStore.get('license');
              if (license && license.tested !== undefined) {
                 result = license.tested;
              }
              else {
                 result = false;
              }
           }
           return result;
           },

       getUser:  function() {
           return $http({
               method: 'GET', 
               url: '/api/v1/me/',
               headers: { 'Authorization': 'Token ' + this.getToken() }
               });
           },

       setUserInfo: function(response) {
           // store the response values in $rootScope so we can get to them later
           $rootScope.current_user = response.results[0];
           $cookieStore.put('current_user', response.results[0]);    //keep in session cookie incase user hits refresh
           },

       restoreUserInfo: function() {
           $rootScope.current_user = $cookieStore.get('current_user');
           },

       getUserInfo: function(key) {
           // Access values returned from the Me API call
           return ($rootScope.current_user[key]) ? $rootScope.current_user[key] : null;
           }
    }
}]);

