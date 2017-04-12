/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import buildGroupsListState from './build-groups-list-state.factory';
import controller from './groups-list.controller';

export default
    angular.module('groupsList', [])
        .factory('buildGroupsListState', buildGroupsListState)
        .controller('GroupsListController', controller);
