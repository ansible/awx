/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './job-results.route.js';
import jobResultsService from './job-results.service';

export default
    angular.module('jobResults', [])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }])
        .service('jobResultsService', jobResultsService);
