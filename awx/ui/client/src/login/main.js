/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import authenticationService from './authentication.service';
import checkAccess from './checkAccess.factory';
import isAdmin from './isAdmin.factory';
import timer from './timer.factory';
import loginRoute from './login.route';
import logoutRoute from './logout.route';
import loginModalDirective from './loginModal.directive';
import thirdPartySignOnDirective from './thirdPartySignOn.directive';

export default
    angular.module('login', [
    ])
    .factory('Authorization', authenticationService)
    .factory('CheckAccess', checkAccess)
    .factory('IsAdmin', isAdmin)
    .factory('Timer', timer)
    .directive('loginModal', loginModalDirective)
    .directive('thirdPartySignOn', thirdPartySignOnDirective)
    .config(['$routeProvider', function($routeProvider) {
        var url = loginRoute.route;
        delete loginRoute.route;
        $routeProvider.when(url, loginRoute);
        url = logoutRoute.route;
        delete logoutRoute.route;
        $routeProvider.when(url, logoutRoute);
    }]);
