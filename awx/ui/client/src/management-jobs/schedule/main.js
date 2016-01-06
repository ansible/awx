/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './schedule.route';
import controller from './schedule.controller';

export default
    angular.module('managementJobsSchedule', [])
        .controller('managementJobsScheduleController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
