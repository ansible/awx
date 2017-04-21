/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import nestedGroupListState from './nested-groups-list-state.factory';
import nestedGroupListDefinition from './nested-groups.list';
import nestedGroupFormDefinition from './nested-groups.form';
import controller from './nested-groups-list.controller';

export default
    angular.module('nestedGroups', [])
    .factory('nestedGroupListState', nestedGroupListState)
    .value('NestedGroupListDefinition', nestedGroupListDefinition)
    .factory('NestedGroupFormDefinition', nestedGroupFormDefinition)
    .controller('NestedGroupsListController', controller);
