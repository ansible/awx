/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';
import InventoriesManage from './inventory-manage.controller';

export default {
    name: 'inventoryManage',
    url: '/inventories/:inventory_id/manage',
    templateUrl: templateUrl('inventories/manage/inventory-manage'),
    controller: InventoriesManage,
    data: {
        activityStream: true,
        activityStreamTarget: 'inventory',
        activityStreamId: 'inventory_id'
    },
    ncyBreadcrumb: {
        label: "INVENTORY MANAGE"
    },
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
