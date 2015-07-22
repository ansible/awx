/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './schedule.route';
import controller from './schedule.controller';

export default
    angular.module('managementJobsSchedule', [])
        .controller('scheduleController', controller)
        .config(['$routeProvider', function($routeProvider) {
             var url = route.route;
             delete route.route;
             $routeProvider.when(url, route);
        }]);
