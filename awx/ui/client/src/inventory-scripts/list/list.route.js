/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'inventoryScripts',
    route: '/inventory_scripts',
    templateUrl: templateUrl('inventory-scripts/list/list'),
    controller: 'inventoryScriptsListController',
    data: {
        activityStream: true,
        activityStreamTarget: 'inventory_script'
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    },
    ncyBreadcrumb: {
        parent: 'setup',
        label: 'INVENTORY SCRIPTS'
    }
};
