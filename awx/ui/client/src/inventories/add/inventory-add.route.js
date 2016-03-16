/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';
import InventoriesAdd from './inventory-add.controller';

export default {
    name: 'inventories.add',
    route: '/add',
    templateUrl: templateUrl('inventories/inventories'),
    controller: InventoriesAdd,
    ncyBreadcrumb: {
        parent: "inventories",
        label: "CREATE INVENTORY"
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
