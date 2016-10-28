/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import InventoryManageService from './inventory-manage.service';
import HostManageService from './hosts/hosts.service';
import GroupManageService from './groups/groups.service';
import hosts from './hosts/main';
import groups from './groups/main';
import adhoc from './adhoc/main';
import copyMove from './copy-move/main';

export default
angular.module('inventoryManage', [
        hosts.name,
        groups.name,
        copyMove.name,
        adhoc.name
    ])
    .service('InventoryManageService', InventoryManageService)
    .service('HostManageService', HostManageService)
    .service('GroupManageService', GroupManageService);
