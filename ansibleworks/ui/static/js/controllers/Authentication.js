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

function Authenticate($scope, $rootScope, $location, Authorization, ToggleClass, Alert)
{
   // Authorization is injected from AuthService found in services.js
  
   if ($location.path() == '/logout') {
      //if logout request, clear AuthToken and user session data 
      Authorization.logout();
   }

   $rootScope.userLoggedIn = false;  //hide the logout link. if you got here, your logged out.
                                     //gets set back to true by Authorization.setToken().
   
   $scope.sessionExpired = Authorization.didSessionExpire();    //Display session timeout message
   $scope.sessionTimeout = ($AnsibleConfig.session_timeout / 60).toFixed(2)

   $('#login-password').bind('keypress', function(e) {
       var code = (e.keyCode ? e.keyCode : e.which);
       if (code == 13) {
          $('#login-button').click();
       }
       });

   // Display the login dialog
   $('#login-modal').modal({ show: true, keyboard: false, backdrop: false });

   $scope.reset = function() { 
       $('#login-form input').each( function(index) { $(this).val(''); });
       };

   // Call the API to get an auth token
   $scope.systemLogin = function(username, password) {
       $('.api-error').empty();
       Authorization.retrieveToken(username, password)
         .success( function(data, status, headers, config) {
             Authorization.setToken(data.token);
             $scope.reset();
             // Get all the profile/access info regarding the logged in user
             Authorization.getUser()
                 .success(function(data, status, headers, config) {
                     $('#login-modal').modal('hide');
                     Authorization.setUserInfo(data);
                     $location.path('/organizations');
                     })
                 .error( function(data, status, headers, config) {
                     Alert('Error', 'Failed to get user data from /api/v1/me. GET status: ' + status);
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
                if ( data.non_field_errors && data.non_field_errors.length > 0 ) { 
                   $rootScope.alertHeader = 'Error!';
                   $rootScope.alertBody = data.non_field_errors[0];
                }
                else {
                   $rootScope.alertHeader = 'Error!';
                   $rootScope.alertBody = 'The login attempt failed with a status of: ' + status;
                }
                $scope.reset();
                $('#alert-modal').modal({ show: true, keyboard: true,  backdrop: 'static' });
             }
             });
       }
}
