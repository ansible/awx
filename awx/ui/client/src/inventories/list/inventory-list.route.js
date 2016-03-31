/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';
import InventoriesList from './inventory-list.controller';

export default {
    name: 'inventories',
    route: '/inventories',
    templateUrl: templateUrl('inventories/inventories'),
    controller: InventoriesList,
    data: {
        activityStream: true,
        activityStreamTarget: 'inventory'
    },
    ncyBreadcrumb: {
        label: "INVENTORIES"
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
