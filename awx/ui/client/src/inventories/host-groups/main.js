/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import controller from './host-groups.controller';
import hostGroupsDefinition from './host-groups.list';
import hostGroupsAssociate from './host-groups-associate/host-groups-associate.directive';

export default
    angular.module('hostGroups', [])
        .value('HostGroupsList', hostGroupsDefinition)
        .directive('hostGroupsAssociate', hostGroupsAssociate)
        .controller('HostGroupsController', controller);
