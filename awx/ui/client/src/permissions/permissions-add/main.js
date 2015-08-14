/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import userRoute from './permissions-user-add.route';
import teamRoute from './permissions-team-add.route';
import controller from './permissions-add.controller';

export default
    angular.module('permissionsAdd', [])
        .controller('addController', controller)
        .config(['$routeProvider', function($routeProvider) {
            var url = userRoute.route;
            delete userRoute.route;
            $routeProvider.when(url, userRoute);
            url = teamRoute.route;
            delete teamRoute.route;
            $routeProvider.when(url, teamRoute);
        }]);
