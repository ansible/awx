/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import list from './completed-jobs.list';

export default
    angular.module('inventoryCompletedJobs', [])
    .factory('InventoryCompletedJobsList', list);
