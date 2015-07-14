/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'inventoryScriptsAdd',
    route: '/inventory_scripts/add',
    templateUrl: '/static/js/inventory-scripts/add/add.partial.html',
    controller: 'addController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
