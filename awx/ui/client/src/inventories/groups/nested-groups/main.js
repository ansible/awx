/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import nestedGroupListDefinition from './nested-groups.list';
import NestedGroupForm from './nested-groups.form';
import controller from './nested-groups-list.controller';
import addController from './nested-groups-add.controller';

export default
    angular.module('nestedGroups', [])
    .value('NestedGroupListDefinition', nestedGroupListDefinition)
    .factory('NestedGroupForm', NestedGroupForm)
    .controller('NestedGroupsListController', controller)
    .controller('NestedGroupsAddController', addController);
