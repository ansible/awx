/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import buildGroupListState from './build-groups-list-state.factory';
import controller from './groups-list.controller';
import InventoryGroupsList from './inventory-groups.list';

export default
    angular.module('groupList', [])
        .factory('buildGroupListState', buildGroupListState)
        .value('InventoryGroupsList', InventoryGroupsList)
        .controller('GroupsListController', controller);
