/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './notification.route';
import controller from './notification.controller';

export default
    angular.module('managementJobsNotifications', [])
        .controller('managementJobsNotificationsController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
