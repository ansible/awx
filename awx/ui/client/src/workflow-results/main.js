/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import workflowStatusBar from './workflow-status-bar/main';
import route from './workflow-results.route.js';
import workflowResultsService from './workflow-results.service';

export default
    angular.module('workflowResults', [workflowStatusBar.name])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }])
        .service('workflowResultsService', workflowResultsService);
