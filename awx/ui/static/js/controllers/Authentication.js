/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Authentication.js
 *
 *  Controller functions for user authentication.
 *
 */

'use strict';

function Authenticate($cookieStore, $window, $scope, $rootScope, $location, Authorization, ToggleClass, Alert, Wait, 
    Timer, Empty)
{
   var setLoginFocus = function() {
      $('#login-username').focus();
      };

   var sessionExpired = function() {
      return (Empty($rootScope.sessionExpired)) ? $cookieStore.get('sessionExpired') : $rootScope.sessionExpired;
      }();
   
   var lastPath = function() {
      return (Empty($rootScope.lastPath)) ? $cookieStore.get('lastPath') : $rootScope.lastPath;
      }();

   if ($AnsibleConfig.debug_mode && console) {
      console.log('User session expired: ' + sessionExpired);
      console.log('Last URL: ' + lastPath);
   }
   
   // Hide any lingering modal dialogs
   $('.modal[aria-hidden=false]').each( function() {
       if ($(this).attr('id') !== 'login-modal') {
          $(this).modal('hide');
       }
       });

   // Just in case, make sure the wait widget is not active
   Wait('stop');
   
   // Display the login dialog
   $('#login-modal').modal({ show: true, keyboard: false, backdrop: 'static' });
   
   // Set focus to username field
   $('#login-modal').on('shown.bs.modal', function() {
       setLoginFocus();
       });

   var scope = angular.element(document.getElementById('login-modal')).scope();
   
   // Reset the login form
   scope['login_username'] = null;
   scope['login_password'] = null;
   scope['loginForm']['login_username'].$setPristine();
   scope['loginForm']['login_password'].$setPristine();

   if ($location.path() == '/logout') {
      //if logout request, clear AuthToken and user session data
      Authorization.logout();
      $location.url('/home');
   }
  
   $rootScope.userLoggedIn = false;             //hide the logout link. if you got here, you're logged out.
   $cookieStore.put('userLoggedIn', false);     //gets set back to true by Authorization.setToken().

   $('#login-password').bind('keypress', function(e) {
       var code = (e.keyCode ? e.keyCode : e.which);
       if (code == 13) {
          $('#login-button').click();
       }
       });
   
   scope.reset = function() { 
       $('#login-form input').each( function(index) { $(this).val(''); });
       };

   // Call the API to get an auth token
   scope.systemLogin = function(username, password) {   
       $('.api-error').empty();
       var token;
       if (username == null || username == undefined || username == '' || 
           password == null || password == undefined || password == '' ) {
           Alert('Error!', 'Please provide a username and password before attempting to login.', 'alert-danger', setLoginFocus);
       }
       else {
           Wait('start');
           Authorization.retrieveToken(username, password)
             .success( function(data, status, headers, config) {
                 Wait('stop');
                 $('#login-modal').modal('hide');
                 token = data.token;
                 Authorization.setToken(data.token, data.expires);
                 $rootScope.sessionTimer = Timer.init();
                 // Get all the profile/access info regarding the logged in user
                 Authorization.getUser()
                     .success(function(data, status, headers, config) {
                         Authorization.setUserInfo(data);
                         $rootScope['user_is_superuser'] = data.results[0].is_superuser;
                         Authorization.getLicense()
                             .success(function(data, status, headers, config) {
                                 Authorization.setLicense(data['license_info']);
                                 if (lastPath) {
                                     // Go back to most recent navigation path
                                     $location.path(lastPath);
                                 }
                                 else {
                                     $location.url('/home?login=true');
                                 }
                                 })
                             .error(function(data, status, headers, config) {
                                 Alert('Error', 'Failed to access user information. GET returned status: ' + status, 'alert-danger', setLoginFocus);
                                 });
                         })
                     .error( function(data, status, headers, config) {
                         Alert('Error', 'Failed to access license information. GET returned status: ' + status, 'alert-danger', setLoginFocus);
                         });
                 })
             .error( function(data, status, headers, config) {
                 Wait('stop');
                 if ( data.non_field_errors && data.non_field_errors.length == 0 ) {
                    // show field specific errors returned by the API
                    for (var key in data) {
                        scope[key + 'Error'] = data[key][0];
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
                    scope.reset();
                    Alert(hdr, msg, 'alert-danger', setLoginFocus);
                 }
                 });
           }
       }
}

Authenticate.$inject = ['$cookieStore', '$window', '$scope', '$rootScope', '$location', 'Authorization', 'ToggleClass', 'Alert', 'Wait',
                        'Timer', 'Empty'];

