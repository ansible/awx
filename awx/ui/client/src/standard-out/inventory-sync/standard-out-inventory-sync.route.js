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
        inventorySyncSocket: [function() {
            // TODO: determine whether or not we have socket support for inventory sync standard out
            return true;
        }]
    }
};
