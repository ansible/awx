/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'inventoryScripts.add',
    route: '/add',
    templateUrl: templateUrl('inventory-scripts/add/add'),
    controller: 'inventoryScriptsAddController',
    ncyBreadcrumb: {
        parent: 'inventoryScripts',
        label: 'CREATE INVENTORY SCRIPT'
    }
};
