/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

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

export default ['$log', '$cookieStore', '$compile', '$window', '$rootScope', '$location', 'Authorization', 'ToggleClass', 'Alert', 'Wait',
    'Timer', 'Empty', 'ClearScope', '$scope', 'pendoService',
    function ($log, $cookieStore, $compile, $window, $rootScope, $location, Authorization, ToggleClass, Alert, Wait,
    Timer, Empty, ClearScope, scope, pendoService) {

    var setLoginFocus, lastPath, lastUser, sessionExpired, loginAgain;

    setLoginFocus = function () {
        // Need to clear out any open dialog windows that might be open when this modal opens.
        ClearScope();
        $('#login-username').focus();
    };

    loginAgain = function() {
        setTimeout(function() {
            $location.path('/logout');
        }, 1000);
    };

    scope.sessionExpired = (Empty($rootScope.sessionExpired)) ? $cookieStore.get('sessionExpired') : $rootScope.sessionExpired;
    scope.login_username = '';
    scope.login_password = '';

    lastPath = function () {
        return (Empty($rootScope.lastPath)) ? $cookieStore.get('lastPath') : $rootScope.lastPath;
    };

    lastUser = function(){
        if(!Empty($rootScope.lastUser) && $rootScope.lastUser === $rootScope.current_user.id){
            return true;
        }
        else {
            return false;
        }
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

    // Set focus to username field
    $('#login-modal').on('shown.bs.modal', function () {
        setLoginFocus();
    });

    $rootScope.loginConfig.promise.then(function () {
        scope.customLogo = ($AnsibleConfig.custom_logo) ? "custom_console_logo.png" : "tower_console_logo.png";
        scope.customLoginInfo = $AnsibleConfig.custom_login_info;
        scope.customLoginInfoPresent = ($AnsibleConfig.customLoginInfo) ? true : false;
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
                pendoService.issuePendoIdentity();
                Wait("stop");
                if (lastPath() && lastUser()) {
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
                Timer.init().then(function(timer){
                    $rootScope.sessionTimer = timer;
                    $rootScope.$emit('OpenSocket');
                    $rootScope.user_is_superuser = data.results[0].is_superuser;
                    scope.$emit('AuthorizationGetLicense');
                });
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
            scope.reset();
            scope.attemptFailed = true;
            $('#login-username').focus();
        } else {
            Wait('start');
            Authorization.retrieveToken(username, password)
                .then(function (data) {
                    $('#login-modal').modal('hide');
                    Authorization.setToken(data.data.token, data.data.expires);
                    scope.$emit('AuthorizationGetUser');
                },
                function (data) {
                    var key;
                    Wait('stop');
                    if (data && data.data && data.data.non_field_errors && data.data.non_field_errors.length === 0) {
                        // show field specific errors returned by the API
                        for (key in data.data) {
                            scope[key + 'Error'] = data.data[key][0];
                        }
                    } else {
                        scope.reset();
                        scope.attemptFailed = true;
                        $('#login-username').focus();
                    }
                });
        }
    };
}];
