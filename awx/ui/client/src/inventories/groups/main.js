/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import groupList from './list/main';
import service from './groups.service';
import GetHostsStatusMsg from './factories/get-hosts-status-msg.factory';
import GetSourceTypeOptions from './factories/get-source-type-options.factory';
import GetSyncStatusMsg from './factories/get-sync-status-msg.factory';
import GroupsCancelUpdate from './factories/groups-cancel-update.factory';
import ViewUpdateStatus from './factories/view-update-status.factory';

export default
    angular.module('group', [
        groupList.name
    ])
    .factory('GetHostsStatusMsg', GetHostsStatusMsg)
    .factory('GetSourceTypeOptions', GetSourceTypeOptions)
    .factory('GetSyncStatusMsg', GetSyncStatusMsg)
    .factory('GroupsCancelUpdate', GroupsCancelUpdate)
    .factory('ViewUpdateStatus', ViewUpdateStatus)
    .service('GroupManageService', service);
