/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import userRoute from './user-edit.route';
import teamRoute from './team-edit.route';
import controller from './edit.controller';

export default
    angular.module('permissionsEdit', [])
        .controller('permissionsEditController', controller)
        .config(['$routeProvider', function($routeProvider) {
            var url = userRoute.route;
            delete userRoute.route;
            $routeProvider.when(url, userRoute);
            url = teamRoute.route;
            delete teamRoute.route;
            $routeProvider.when(url, teamRoute);
        }]);
