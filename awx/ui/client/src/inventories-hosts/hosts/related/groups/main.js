/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import controller from './hosts-related-groups.controller';
import hostGroupsDefinition from './hosts-related-groups.list';


export default
    angular.module('hostGroups', [])
        .factory('HostsRelatedGroupsList', hostGroupsDefinition)
        .controller('HostsRelatedGroupsController', controller);
