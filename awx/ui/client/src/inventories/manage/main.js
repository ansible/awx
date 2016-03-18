/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './inventory-manage.route';
import controller from './inventory-manage.controller';

import manageHostsDirective from './manage-hosts/manage-hosts.directive';
import manageHostsRoute from './manage-hosts/manage-hosts.route';

export default
angular.module('inventoryManage', [])
    .directive('manageHosts', manageHostsDirective)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(route);
        $stateExtender.addState(manageHostsRoute);
    }]);
