/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './manage-groups.route';
import manageGroupsDirective from './directive/manage-groups.directive';

export default
    angular.module('manage-groups', [])
    .directive('manageGroups', manageGroupsDirective)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route.edit);
            $stateExtender.addState(route.add);
        }]);
