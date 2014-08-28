/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Authentication.js
 *
 *  Controller functions for user authentication.
 *
 */
/**
 * @ngdoc function
 * @name controllers.function:Authentication
 * @description This controller's for authenticating users
*/
'use strict';

function Authenticate($log, $cookieStore, $compile, $window, $scope, $rootScope, $location, Authorization, ToggleClass, Alert, Wait,
    Timer, Empty) {

    var setLoginFocus, lastPath, sessionExpired, loginAgain,
        e, html, scope = $rootScope.$new();

    setLoginFocus = function () {
        $('#login-username').focus();
    };

    loginAgain = function() {
        Authorization.logout();
        setTimeout(function() {
            //$location.url('/logout');
            window.location = '/#/logout';  // if we get here, force user back to re-login
        }, 1000);
    };

    scope.sessionExpired = (Empty($rootScope.sessionExpired)) ? $cookieStore.get('sessionExpired') : $rootScope.sessionExpired;
    scope.login_username = '';
    scope.login_password = '';

    lastPath = function () {
        return (Empty($rootScope.lastPath)) ? $cookieStore.get('lastPath') : $rootScope.lastPath;
    };

    $log.debug('User session expired: ' + sessionExpired);
    $log.debug('Last URL: ' + lastPath());

    // Hide any lingering modal dialogs
    $('.modal[aria-hidden=false]').each(function () {
        if ($(this).attr('id') !== 'login-modal') {
            $(this).modal('hide');
        }
    });

    // Just in case, make sure the wait widget is not active
    // and scroll the window to the top
    Wait('stop');
    window.scrollTo(0,0);

    if ($location.path() === '/logout') {
        //if logout request, clear AuthToken and user session data
        Authorization.logout();
    }

    e = angular.element(document.getElementById('login-modal-content'));
    html = "<div class=\"modal-header login-header\">\n" +
        "<img src=\"" + $basePath + "img/tower_console_logo.png\" />" +
        "</div>\n" +
        "<div class=\"modal-body\" id=\"login-modal-body\">\n" +
        "<div class=\"login-alert\" ng-show=\"!sessionExpired\">Welcome to Ansible Tower! &nbsp;Please sign in.</div>\n" +
        "<div class=\"login-alert\" ng-show=\"sessionExpired\">Your session timed out due to inactivity. Please sign in.</div>\n" +
        "<form id=\"login-form\" name=\"loginForm\" class=\"form-horizontal\" autocomplete=\"off\" novalidate >\n" +
        "<div class=\"form-group\">\n" +
        "<label class=\"control-label col-md-offset-1 col-md-2 col-sm-offset-1 col-sm-2 col-xs-3 prepend-asterisk\">Username</label>\n" +
        "<div class=\"col-md-8 col-sm-8 col-xs-9\">\n" +
        "<input type=\"text\" name=\"login_username\" class=\"form-control\" ng-model=\"login_username\"" +
        "id=\"login-username\" autocomplete=\"off\" required>\n" +
        "<div class=\"error\" ng-show=\"loginForm.login_username.$dirty && loginForm.login_username.$error.required\">A value is required!</div>\n" +
        "<div class=\"error api-error\" ng-bind=\"usernameError\"></div>\n" +
        "</div>\n" +
        "</div>\n" +
        "<div class=\"form-group\">\n" +
        "<label class=\"control-label col-md-offset-1 col-md-2 col-sm-offset-1 col-sm-2 col-xs-3 prepend-asterisk\">Password</label>\n" +
        "<div class=\"col-md-8 col-sm-8 col-xs-9\">\n" +
        "<input type=\"password\" name=\"login_password\" id=\"login-password\" class=\"form-control\"" +
        "ng-model=\"login_password\" required autocomplete=\"off\">\n" +
        "<div class=\"error\" ng-show=\"loginForm.login_password.$dirty && loginForm.login_password.$error.required\">A value is required!</div>\n" +
        "<div class=\"error api-error\" ng-bind=\"passwordError\"></div>\n" +
        "</div>\n" +
        "</div>\n" +
        "</form>\n" +
        "</div>\n" +
        "<div class=\"modal-footer\">\n" +
        "<button ng-click=\"systemLogin(login_username, login_password)\" id=\"login-button\" class=\"btn btn-primary\"><i class=\"fa fa-sign-in\"></i> Sign In</button>\n" +
        "</div>\n";
    e.empty().html(html);
    $compile(e)(scope);

    // Set focus to username field
    $('#login-modal').on('shown.bs.modal', function () {
        setLoginFocus();
    });

    // Display the login dialog
    $('#login-modal').modal({
        show: true,
        keyboard: false,
        backdrop: 'static'
    });

    // Reset the login form
    //scope.loginForm.login_username.$setPristine();
    //scope.loginForm.login_password.$setPristine();
    //$rootScope.userLoggedIn = false; //hide the logout link. if you got here, you're logged out.
    //$cookieStore.put('userLoggedIn', false); //gets set back to true by Authorization.setToken().

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
                Alert('Error', 'Failed to access license information. GET returned status: ' + status, 'alert-danger', loginAgain);
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
                Authorization.logout();
                Wait('stop');
                Alert('Error', 'Failed to access user information. GET returned status: ' + status, 'alert-danger', loginAgain);
            });
    });

    // Call the API to get an cauth token
    scope.systemLogin = function (username, password) {
        $('.api-error').empty();
        var token;
        if (Empty(username) || Empty(password)) {
            Alert('Error!', 'Please provide a username and password before attempting to login.', 'alert-danger', setLoginFocus, null, null, false);
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
                .error(function (data) {
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
                        }
                        else {
                            hdr = 'Error';
                            msg = 'The login attempt failed. The Tower server is not responding. Check that the Tower server processes are running' +
                            ' and accessible.';
                        }
                        scope.reset();
                        Alert(hdr, msg, 'alert-danger', setLoginFocus, null, null, false);
                    }
                });
        }
    };
}

Authenticate.$inject = ['$log', '$cookieStore', '$compile', '$window', '$scope', '$rootScope', '$location', 'Authorization', 'ToggleClass', 'Alert', 'Wait',
    'Timer', 'Empty'
];
