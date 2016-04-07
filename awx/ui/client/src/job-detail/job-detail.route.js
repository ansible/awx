/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';
import HostSummaryController from './host-summary/host-summary.controller';

export default {
    name: 'jobDetail',
    url: '/jobs/:id',
    ncyBreadcrumb: {
        parent: 'jobs',
        label: "{{ job.id }} - {{ job.name }}"
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        jobEventsSocket: ['Socket', '$rootScope', function(Socket, $rootScope) {
            if (!$rootScope.event_socket) {
                $rootScope.event_socket = Socket({
                    scope: $rootScope,
                    endpoint: "job_events"
                });
                $rootScope.event_socket.init();
                // returns should really be providing $rootScope.event_socket
                // otherwise, we have to inject the entire $rootScope into the controller
                return true;
            } else {
                return true;
            }
        }],
        jobSocket: ['Socket', '$rootScope', function(Socket, $rootScope) {
            var job_socket = Socket({
                    scope: $rootScope,
                    endpoint: "jobs"
            });
            job_socket.init();
                // returns should really be providing $rootScope.job_socket
                // otherwise, we have to inject the entire $rootScope into the controller
            return job_socket;
        }]
    },
    views: {
        '': {
            templateUrl: templateUrl('job-detail/job-detail'),
            controller: 'JobDetailController',
        },
        'host-summary@jobDetail': {
            templateUrl: templateUrl('job-detail/host-summary/host-summary'),
            controller: HostSummaryController
        }
    }
};
