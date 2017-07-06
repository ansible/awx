/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import nestedGroupListDefinition from './group-nested-groups.list';
import controller from './group-nested-groups-list.controller';
import addController from './group-nested-groups-add.controller';
import NestedGroupForm from './group-nested-groups.form';

export default
    angular.module('nestedGroups', [])
    .factory('NestedGroupForm', NestedGroupForm)
    .factory('NestedGroupListDefinition', nestedGroupListDefinition)
    .controller('NestedGroupsListController', controller)
    .controller('NestedGroupsAddController', addController);
