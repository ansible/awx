/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import GroupAddController from './groups-add.controller';
import GroupEditController from './groups-edit.controller';

export default
angular.module('manageGroups', [])
    .controller('GroupAddController', GroupAddController)
    .controller('GroupEditController', GroupEditController);
