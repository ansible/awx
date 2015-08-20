/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import userRoute from './user-add.route';
import teamRoute from './team-add.route';
import controller from './add.controller';

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
