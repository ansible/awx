/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import list from './completed_jobs.list';

export default
    angular.module('inventoryCompletedJobs', [])
    .factory('InventoryCompletedJobsList', list);
