/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import GroupAddController from './groups-add.controller';
import GroupEditController from './groups-edit.controller';
import GetHostsStatusMsg from './factories/get-hosts-status-msg.factory';
import GetSourceTypeOptions from './factories/get-source-type-options.factory';
import GetSyncStatusMsg from './factories/get-sync-status-msg.factory';
import GroupsCancelUpdate from './factories/groups-cancel-update.factory';
import ViewUpdateStatus from './factories/view-update-status.factory';
import InventoryGroups from './inventory-groups.list';
import GroupForm from './groups.form';

export default
angular.module('manageGroups', [])
    .factory('GetHostsStatusMsg', GetHostsStatusMsg)
    .factory('GetSourceTypeOptions', GetSourceTypeOptions)
    .factory('GetSyncStatusMsg', GetSyncStatusMsg)
    .factory('GroupsCancelUpdate', GroupsCancelUpdate)
    .factory('ViewUpdateStatus', ViewUpdateStatus)
    .factory('GroupForm', GroupForm)
    .value('InventoryGroups', InventoryGroups)
    .controller('GroupAddController', GroupAddController)
    .controller('GroupEditController', GroupEditController);
