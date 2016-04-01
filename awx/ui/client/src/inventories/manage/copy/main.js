/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './copy.route';
import copyGroupsDirective from './copy-groups-directive/copy-groups.directive';
import copyHostsDirective from './copy-hosts-directive/copy-hosts.directive';

export default
angular.module('inventory-copy', [])
    .directive('copyGroups', copyGroupsDirective)
    .directive('copyHosts', copyHostsDirective)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(route.copy);
        $stateExtender.addState(route.copyGroup);
        $stateExtender.addState(route.copyHost);
    }]);
