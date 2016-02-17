/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'jobDetail',
    url: '/jobs/:id',
    templateUrl: templateUrl('job-detail/job-detail'),
    controller: 'JobDetailController',
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
                return true;
            } else {
                return true;
            }
        }]
    }
};
