/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import buildGroupsEditState from './build-groups-edit-state.factory';
import controller from './groups-edit.controller';

export default
angular.module('groupEdit', [])
    .factory('buildGroupsEditState', buildGroupsEditState)
    .controller('GroupEditController', controller);
