/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './inventory-manage.route';

import manageHosts from './manage-hosts/main';
import manageGroups from './manage-groups/main';

export default
angular.module('inventoryManage', [
        manageHosts.name,
        manageGroups.name
    ])
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(route);
    }]);
