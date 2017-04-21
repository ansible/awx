/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import list from './completed_jobs.list';
import buildInventoryCompletedJobsState from './build-inventory-completed-jobs-state.factory';

export default
    angular.module('inventoryCompletedJobs', [])
    .factory('InventoryCompletedJobsList', list)
    .factory('buildInventoryCompletedJobsState', buildInventoryCompletedJobsState);
