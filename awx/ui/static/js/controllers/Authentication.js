/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Authentication.js
 *
 *  Controller functions for user authentication.
 *
 */

 /* globals console:false */

'use strict';

function Authenticate($cookieStore, $compile, $window, $scope, $rootScope, $location, Authorization, ToggleClass, Alert, Wait,
    Timer, Empty) {

    var setLoginFocus, lastPath, sessionExpired,
        e, scope = $rootScope.$new();

    setLoginFocus = function () {
        $('#login-username').focus();
    };

    sessionExpired = (Empty($rootScope.sessionExpired)) ? $cookieStore.get('sessionExpired') : $rootScope.sessionExpired;

    lastPath = function () {
        return (Empty($rootScope.lastPath)) ? $cookieStore.get('lastPath') : $rootScope.lastPath;
    };

    if ($AnsibleConfig.debug_mode && console) {
        console.log('User session expired: ' + sessionExpired);
        console.log('Last URL: ' + lastPath());
    }

    // Hide any lingering modal dialogs
    $('.modal[aria-hidden=false]').each(function () {
        if ($(this).attr('id') !== 'login-modal') {
            $(this).modal('hide');
        }
    });

    // Just in case, make sure the wait widget is not active
    Wait('stop');

    // Display the login dialog
    $('#login-modal').modal({
        show: true,
        keyboard: false,
        backdrop: 'static'
    });

    // Set focus to username field
    $('#login-modal').on('shown.bs.modal', function () {
        setLoginFocus();
    });

    e = angular.element(document.getElementById('login-modal'));
    $compile(e)(scope);

    // Reset the login form
    scope.login_username = null;
    scope.login_password = null;
    scope.loginForm.login_username.$setPristine();
    scope.loginForm.login_password.$setPristine();

    if ($location.path() === '/logout') {
        //if logout request, clear AuthToken and user session data
        Authorization.logout();
    }

    $rootScope.userLoggedIn = false; //hide the logout link. if you got here, you're logged out.
    $cookieStore.put('userLoggedIn', false); //gets set back to true by Authorization.setToken().

    $('#login-password').bind('keypress', function (e) {
        var code = (e.keyCode ? e.keyCode : e.which);
        if (code === 13) {
            $('#login-button').click();
        }
    });

    scope.reset = function () {
        $('#login-form input').each(function () {
            $(this).val('');
        });
    };

    if (scope.removeAuthorizationGetLicense) {
        scope.removeAuthorizationGetLicense();
    }
    scope.removeAuthorizationGetLicense = scope.$on('AuthorizationGetLicense', function() {
        Authorization.getLicense()
            .success(function (data) {
                Authorization.setLicense(data);
                if (lastPath()) {
                    // Go back to most recent navigation path
                    $location.path(lastPath());
                } else {
                    $location.url('/home?login=true');
                }
            })
            .error(function () {
                Wait('stop');
                Alert('Error', 'Failed to access license information. GET returned status: ' + status, 'alert-danger', setLoginFocus);
            });
    });

    if (scope.removeAuthorizationGetUser) {
        scope.removeAuthorizationGetUser();
    }
    scope.removeAuthorizationGetUser = scope.$on('AuthorizationGetUser', function() {
        // Get all the profile/access info regarding the logged in user
        Authorization.getUser()
            .success(function (data) {
                Authorization.setUserInfo(data);
                $rootScope.user_is_superuser = data.results[0].is_superuser;
                scope.$emit('AuthorizationGetLicense');
            })
            .error(function (data, status) {
                Wait('stop');
                Alert('Error', 'Failed to access user information. GET returned status: ' + status, 'alert-danger', setLoginFocus);
            });
    });

    // Call the API to get an cauth token
    scope.systemLogin = function (username, password) {
        $('.api-error').empty();
        var token;
        if (Empty(username) || Empty(password)) {
            Alert('Error!', 'Please provide a username and password before attempting to login.', 'alert-danger', setLoginFocus);
        } else {
            Wait('start');
            Authorization.retrieveToken(username, password)
                .success(function (data) {
                    $('#login-modal').modal('hide');
                    token = data.token;
                    Authorization.setToken(data.token, data.expires);
                    $rootScope.sessionTimer = Timer.init();
                    scope.$emit('AuthorizationGetUser');
                })
                .error(function (data, status) {
                    var hdr, msg, key;
                    Wait('stop');
                    if (data.non_field_errors && data.non_field_errors.length === 0) {
                        // show field specific errors returned by the API
                        for (key in data) {
                            scope[key + 'Error'] = data[key][0];
                        }
                    } else {
                        if (data.non_field_errors && data.non_field_errors.length > 0) {
                            hdr = 'Error';
                            msg = data.non_field_errors[0];
                        } else {
                            hdr = 'Error';
                            msg = 'The login attempt failed with a status of: ' + status;
                        }
                        scope.reset();
                        Alert(hdr, msg, 'alert-danger', setLoginFocus);
                    }
                });
        }
    };
}

Authenticate.$inject = ['$cookieStore', '$compile', '$window', '$scope', '$rootScope', '$location', 'Authorization', 'ToggleClass', 'Alert', 'Wait',
    'Timer', 'Empty'
];
