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
 * @description
 * Controller for handling /#/login and /#/logout routes.
 *
 * Tower (app.js) verifies the user is authenticated and that the user session is not expired. If either condition is not true,
 * the user is redirected to /#/login and the Authentication controller.
 *
 * Methods for checking the session state are found in [js/shared/AuthService.js](/static/docs/api/shared.function:AuthService), which is referenced here as Authorization.
 *
 * #Login Modal Dialog
 *
 * The modal dialog prompting for username and password is found in templates/ui/index.html.
 *```
 *     <!-- login modal -->
 *     <div id="login-modal" class="modal fade">
 *         <div class="modal-dialog">
 *             <div class="modal-content" id="login-modal-content">
 *             </div><!-- modal-content -->
 *         </div><!-- modal-dialog -->
 *     </div><!-- modal -->
 *```
 * HTML for the login form is generated, compiled and injected into <div id="login-modal-content"></div> by the controller. This is done to associate the form with the controller's scope. Because
 * <div id="login-modal"></div> is outside of the ng-view container, it gets associated with $rootScope by default. In the controller we create a new scope using $rootScope.$new() and associate
 * that with the login form. Doing this each time the controller is instantiated insures the form is clean and not pre-populated with a prior user's username and password.
 *
 * Just before the release of 2.0 a bug was discovered where clicking logout and then immediately clicking login without providing a username and password would successfully log
 * the user back into Tower. Implementing the above approach fixed this, forcing a new username/password to be entered each time the login dialog appears.
 *
 * #Login Workflow
 *
 * When the the login button is clicked, the following occurs:
 *
 * - Call Authorization.retrieveToken(username, password) - sends a POST request to /api/v1/authtoken to get a new token value.
 * - Call Authorization.setToken(token, expires) to store the token and exipration time in a session cookie.
 * - Start the expiration timer by calling the init() method of [js/shared/Timer.js](/static/docs/api/shared.function:Timer)
 * - Get user informaton by calling Authorization.getUser() - sends a GET request to /api/v1/me
 * - Store user information in the session cookie by calling Authorization.setUser().
 * - Get the Tower license by calling Authorization.getLicense() - sends a GET request to /api/vi/config
 * - Stores the license object in local storage by calling Authorization.setLicense(). This adds the Tower version and a tested flag to the license object. The tested flag is initially set to false.
 *
 * Note that there is a session timer kept on the server side as well as the client side. Each time an API request is made, Tower (in app.js) calls
 * Timer.isExpired(). This verifies the UI does not think the session is expired, and if not, moves the expiration time into the future. The number of
 * seconds between API calls before a session is considered expired is set in config.js as session_timeout.
 *
 * @Usage
 * This is usage information.
 */


export function Authenticate($log, $cookieStore, $compile, $window, $rootScope, $location, Authorization, ToggleClass, Alert, Wait,
    Timer, Empty, ClearScope) {

    var setLoginFocus, lastPath, sessionExpired, loginAgain,
        e, html, scope = $rootScope.$new();

    setLoginFocus = function () {
        // Need to clear out any open dialog windows that might be open when this modal opens.
        ClearScope();
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
        "<label class=\"control-label col-md-offset-1 col-md-2 col-sm-offset-1 col-sm-2 col-xs-3 prepend-asterisk prepend-asterisk--login\">Username</label>\n" +
        "<div class=\"col-md-8 col-sm-8 col-xs-9\">\n" +
        "<input type=\"text\" name=\"login_username\" class=\"form-control\" ng-model=\"login_username\"" +
        "id=\"login-username\" autocomplete=\"off\" required>\n" +
        "<div class=\"error\" ng-show=\"loginForm.login_username.$dirty && loginForm.login_username.$error.required\">Please enter a username.</div>\n" +
        "<div class=\"error api-error\" ng-bind=\"usernameError\"></div>\n" +
        "</div>\n" +
        "</div>\n" +
        "<div class=\"form-group\">\n" +
        "<label class=\"control-label col-md-offset-1 col-md-2 col-sm-offset-1 col-sm-2 col-xs-3 prepend-asterisk prepend-asterisk--login\">Password</label>\n" +
        "<div class=\"col-md-8 col-sm-8 col-xs-9\">\n" +
        "<input type=\"password\" name=\"login_password\" id=\"login-password\" class=\"form-control\"" +
        "ng-model=\"login_password\" required autocomplete=\"off\">\n" +
        "<div class=\"error\" ng-show=\"loginForm.login_password.$dirty && loginForm.login_password.$error.required\">Please enter a password.</div>\n" +
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

    // Call the API to get an auth token
    scope.systemLogin = function (username, password) {
        $('.api-error').empty();
        if (Empty(username) || Empty(password)) {
            Alert('Error!', 'Please provide a username and password before attempting to login.', 'alert-danger', setLoginFocus, null, null, false);
        } else {
            Wait('start');
            Authorization.retrieveToken(username, password)
                .success(function (data) {
                    $('#login-modal').modal('hide');
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

Authenticate.$inject = ['$log', '$cookieStore', '$compile', '$window', '$rootScope', '$location', 'Authorization', 'ToggleClass', 'Alert', 'Wait',
    'Timer', 'Empty', 'ClearScope'
];
