/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './manage-hosts.route';
import manageHostsDirective from './directive/manage-hosts.directive';

export default
    angular.module('manage-hosts', [])
    .directive('manageHosts', manageHostsDirective)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route.edit);
            $stateExtender.addState(route.add);
        }]);
