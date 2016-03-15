/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './job-detail.route';
import controller from './job-detail.controller';
import service from './job-detail.service';

export default
    angular.module('jobDetail', [])
        .controller('JobDetailController', controller)
        .service('JobDetailService', service)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
