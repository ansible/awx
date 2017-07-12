/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import HostNestedGroupListDefinition from './host-nested-groups.list';
import HostNestedGroupsListController from './host-nested-groups-list.controller';

export default
    angular.module('hostNestedGroups', [])
    .factory('HostNestedGroupListDefinition', HostNestedGroupListDefinition)
    .controller('HostNestedGroupsListController', HostNestedGroupsListController);
