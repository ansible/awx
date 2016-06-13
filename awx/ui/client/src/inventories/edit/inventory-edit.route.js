/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';
import InventoriesEdit from './inventory-edit.controller';

export default {
    name: 'inventories.edit',
    route: '/:inventory_id',
    templateUrl: templateUrl('inventories/inventories'),
    controller: InventoriesEdit,
    data: {
        activityStreamId: 'inventory_id'
    },
    ncyBreadcrumb: {
        parent: 'inventories',
        label: "{{inventory_obj.name}}"
    }
};
