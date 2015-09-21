/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import authentication from './authenticationServices/main';
import loginModal from './loginModal/main';

import loginRoute from './login.route';
import logoutRoute from './logout.route';
import pendoService from './pendo/pendo.service';

export default
    angular.module('login', [authentication.name, loginModal.name])
        .service('pendoService', pendoService)
        .config(['$routeProvider', function($routeProvider) {
            var url = loginRoute.route;
            delete loginRoute.route;
            $routeProvider.when(url, loginRoute);
            url = logoutRoute.route;
            delete logoutRoute.route;
            $routeProvider.when(url, logoutRoute);
        }]);
