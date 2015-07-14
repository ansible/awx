/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'inventoryScriptsList',
    route: '/inventory_scripts',
    templateUrl: '/static/js/inventory-scripts/list/list.partial.html',
    controller: 'listController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
