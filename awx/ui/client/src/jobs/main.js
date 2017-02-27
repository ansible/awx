/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobsList from './jobs-list.controller';
import jobsRoute from './jobs.route';

export default
    angular.module('JobsModule', [])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(jobsRoute);
        }])
        .controller('JobsList', jobsList);
