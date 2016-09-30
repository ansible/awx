/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import hostStatusBar from './host-status-bar/main';

import route from './job-results.route.js';

import jobResultsService from './job-results.service';
import eventQueueService from './event-queue.service';

import durationFilter from './duration.filter';

export default
    angular.module('jobResults', [hostStatusBar.name])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }])
        .service('jobResultsService', jobResultsService)
        .service('eventQueue', eventQueueService)
        .filter('duration', durationFilter);
