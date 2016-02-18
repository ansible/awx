/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'managementJobStdout',
    route: '/management_jobs/:id/stdout',
    templateUrl: templateUrl('standard-out/management-jobs/standard-out-management-jobs'),
    controller: 'JobStdoutController',
    data: {
        jobType: 'system_jobs'
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        adhocEventsSocket: ['Socket', '$rootScope', function(Socket, $rootScope) {
            // if (!$rootScope.adhoc_event_socket) {
            //     $rootScope.adhoc_event_socket = Socket({
            //         scope: $rootScope,
            //         endpoint: "ad_hoc_command_events"
            //     });
            //     $rootScope.adhoc_event_socket.init();
            //     return true;
            // } else {
            //     return true;
            // }

            return true;
        }]
    }
};
