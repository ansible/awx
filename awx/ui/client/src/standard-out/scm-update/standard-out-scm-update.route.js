/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

// TODO: figure out what this route should be - should it be scm_update?

export default {
    name: 'scmUpdateStdout',
    route: '/scm_update/:id/stdout',
    templateUrl: templateUrl('standard-out/scm-update/standard-out-scm-update'),
    controller: 'JobStdoutController',
    data: {
        jobType: 'project_updates'
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
