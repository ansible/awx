/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Authentication.js
 *
 *  Controller functions for user authentication.
 *
 */

'use strict';

function Authenticate($window, $scope, $rootScope, $location, Authorization, ToggleClass, Alert)
{
   // Authorization is injected from AuthService found in services.js
  
   if ($location.path() == '/logout') {
      //if logout request, clear AuthToken and user session data
      Authorization.logout();
   }

   $scope.sessionTimeout = ($AnsibleConfig.session_timeout / 60).toFixed(2);
   $scope.AWXLoginLogo = $staticURL + 'img/AWX_logo.png';
   
   if ($rootScope.userLoggedIn) { 
      // If we're logged in, check for session timeout
      $scope.sessionExpired = Authorization.didSessionExpire();
   }
   else {
      $scope.sessionExpired = false;
   }

   $rootScope.userLoggedIn = false;  //hide the logout link. if you got here, you're logged out.
                                     //gets set back to true by Authorization.setToken().

   $('#login-password').bind('keypress', function(e) {
       var code = (e.keyCode ? e.keyCode : e.which);
       if (code == 13) {
          $('#login-button').click();
       }
       });

   // Display the login dialog
   $('#login-modal').modal({ show: true, keyboard: false, backdrop: 'static' });

   $scope.reset = function() { 
       $('#login-form input').each( function(index) { $(this).val(''); });
       };

   // Call the API to get an auth token
   $scope.systemLogin = function(username, password) {   
       $('.api-error').empty();
       var token;
       Authorization.retrieveToken(username, password)
         .success( function(data, status, headers, config) {
             token = data.token;
             Authorization.setToken(data.token);
             $scope.reset();

             // Force request to /organizations to query with the correct token -in the event a new user
             // has logged in.
             var today = new Date();
             today.setTime(today.getTime() + ($AnsibleConfig.session_timeout * 1000));
             $rootScope.token = token;
             $rootScope.userLoggedIn = true;
             $rootScope.token_expire = today.getTime();
             
             // Get all the profile/access info regarding the logged in user
             Authorization.getUser()
                 .success(function(data, status, headers, config) {
                     $('#login-modal').modal('hide');
                     Authorization.setUserInfo(data);
                     Authorization.getLicense()
                         .success(function(data, status, headers, config) {
                             Authorization.setLicense(data['license_info']);
                             $location.path('/organizations');
                             })
                         .error(function(data, status, headers, config) {
                             Alert('Error', 'Failed to access user information. GET returned status: ' + status);
                             });
                     })
                 .error( function(data, status, headers, config) {
                     Alert('Error', 'Failed to access license information. GET returned status: ' + status);
                     });
             })
         .error( function(data, status, headers, config) {
             if ( data.non_field_errors && data.non_field_errors.length == 0 ) {
                // show field specific errors returned by the API
                for (var key in data) {
                    $scope[key + 'Error'] = data[key][0];
                }
             }
             else {
                var hdr, msg;
                if ( data.non_field_errors && data.non_field_errors.length > 0 ) {
                   hdr = 'Error';
                   msg = data.non_field_errors[0];
                }
                else {
                   hdr = 'Error';
                   msg = 'The login attempt failed with a status of: ' + status;
                }
                $scope.reset();
                Alert(hdr, msg);
             }
             });
       }
}

Authenticate.$inject = ['$window', '$scope', '$rootScope', '$location', 'Authorization', 'ToggleClass', 'Alert'];

