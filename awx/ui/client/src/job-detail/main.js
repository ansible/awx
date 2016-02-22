/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './job-detail.route';
import controller from './job-detail.controller';

export default
    angular.module('jobDetail', [])
        .controller('JobDetailController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
