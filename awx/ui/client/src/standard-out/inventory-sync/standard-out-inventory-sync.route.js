/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

// TODO: figure out what this route should be - should it be inventory_sync?

export default {
    name: 'inventorySyncStdout',
    route: '/inventory_sync/:id',
    templateUrl: templateUrl('standard-out/inventory-sync/standard-out-inventory-sync'),
    controller: 'JobStdoutController',
    ncyBreadcrumb: {
        parent: "jobs",
        label: "{{ inventory_source_name }}"
    },
    data: {
        jobType: 'inventory_updates'
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
