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
 * (app.js) verifies the user is authenticated and that the user session is not expired. If either condition is not true,
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
 * the user back into the app. Implementing the above approach fixed this, forcing a new username/password to be entered each time the login dialog appears.
 *
 *
 * @Usage
 * This is usage information.
 */

export default ['$log', '$cookies', '$rootScope', 'ProcessErrors',
    '$location', 'Authorization', 'Alert', 'Wait', 'Timer',
    'Empty', '$scope', 'pendoService', 'ConfigService',
    'CheckLicense', 'SocketService', 'Rest', 'GetBasePath', 'i18n',
    function ($log, $cookies, $rootScope, ProcessErrors,
        $location, Authorization, Alert, Wait, Timer,
        Empty, scope, pendoService, ConfigService,
        CheckLicense, SocketService, Rest, GetBasePath, i18n) {
    var lastPath, lastUser, sessionExpired, loginAgain, preAuthUrl;

    loginAgain = function() {
        setTimeout(function() {
            $location.path('/logout');
        }, 1000);
    };

    scope.sessionExpired = (Empty($rootScope.sessionExpired)) ? $cookies.get('sessionExpired') : $rootScope.sessionExpired;
    scope.login_username = '';
    scope.login_password = '';


    lastPath = function () {
        return (Empty($rootScope.lastPath)) ? $cookies.get('lastPath') : $rootScope.lastPath;
    };

    lastUser = function(){
        if(!Empty($rootScope.lastUser) && $rootScope.lastUser === $rootScope.current_user.id){
            return true;
        }
        else {
            return false;
        }
    };

    preAuthUrl = $rootScope.preAuthUrl;

    $log.debug('User session expired: ' + sessionExpired);
    $log.debug('Last URL: ' + lastPath());

    $rootScope.loginConfig.promise.then(function () {
        if ($AnsibleConfig.custom_logo) {
            scope.customLogo = $rootScope.custom_logo;
            scope.customLogoPresent = true;
        } else {
            scope.customLogo = "logo-login.svg";
            scope.customLogoPresent = false;
        }
        scope.customLoginInfo = $AnsibleConfig.custom_login_info;
        scope.customLoginInfoPresent = (scope.customLoginInfo) ? true : false;
        scope.customLoginInfoIsHTML = /<\/?[a-z][\s\S]*>/i.test(scope.customLoginInfo);
    });

    if (scope.removeAuthorizationGetLicense) {
        scope.removeAuthorizationGetLicense();
    }
    scope.removeAuthorizationGetLicense = scope.$on('AuthorizationGetLicense', function() {
        ConfigService.getConfig().then(function(){
                CheckLicense.test();
                pendoService.issuePendoIdentity();
                Wait("stop");
                if(!Empty(preAuthUrl)){
                    $location.path(preAuthUrl);
                    delete $rootScope.preAuthUrl;
                }
                else {
                    if (lastPath() && lastUser()) {
                        // Go back to most recent navigation path
                        $location.path(lastPath());
                    } else {
                        $location.url('/home');
                    }
                }
            })
            .catch(function () {
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
            .then(({data}) => {
                Authorization.setUserInfo(data);
                Timer.init().then(function(timer){
                    $rootScope.sessionTimer = timer;
                    SocketService.init();
                    $rootScope.user_is_superuser = data.results[0].is_superuser;
                    $rootScope.user_is_system_auditor = data.results[0].is_system_auditor;
                    scope.$emit('AuthorizationGetLicense');
                });

                Rest.setUrl(`${GetBasePath('workflow_approvals')}?status=pending&page_size=1`);
                Rest.get()
                    .then(({data}) => {
                        $rootScope.pendingApprovalCount = data.count;
                    })
                    .catch(({data, status}) => {
                        ProcessErrors({}, data, status, null, {
                            hdr: i18n._('Error!'),
                            msg: i18n._('Failed to get workflow jobs pending approval. GET returned status: ') + status
                        });
                    });
            })
            .catch(({data, status}) => {
                Authorization.logout().then( () => {
                    Wait('stop');
                    Alert('Error', 'Failed to access user information. GET returned status: ' + status, 'alert-danger', loginAgain);
                });
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
                    Authorization.setToken(data.data.expires);
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
