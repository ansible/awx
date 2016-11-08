/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


import route from './workflow-results.route.js';

import workflowResultsService from './workflow-results.service';

export default
    angular.module('workflowResults', [])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }])
        .service('workflowResultsService', workflowResultsService);
