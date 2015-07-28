/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'inventoryScriptsAdd',
    route: '/inventory_scripts/add',
    templateUrl: templateUrl('inventory-scripts/add/add'),
    controller: 'addController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
