/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import buildGroupAddState from './build-groups-add-state.factory';
import controller from './groups-add.controller';

export default
angular.module('groupAdd', [])
    .factory('buildGroupsAddState', buildGroupAddState)
    .controller('GroupAddController', controller);
