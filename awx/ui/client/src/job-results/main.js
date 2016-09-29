/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './job-results.route.js';
import jobResultsService from './job-results.service';
import hostStatusBarDirective from './host-status-bar/main';
import durationFilter from './duration.filter';

export default
    angular.module('jobResults', [hostStatusBarDirective.name])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }])
        .service('jobResultsService', jobResultsService)
        .filter('duration', durationFilter);
