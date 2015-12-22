/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './list.route';
import controller from './list.controller';

export default
    angular.module('managementJobsList', [])
        .controller('managementJobsListController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
