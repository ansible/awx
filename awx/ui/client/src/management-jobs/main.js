/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import managementJobsList from './list/main';
import managementJobsSchedule from './schedule/main';
import list from './management-jobs.list';

export default
    angular.module('managementJobs', [
        managementJobsList.name,
        managementJobsSchedule.name
    ])
    .factory('managementJobsListObject', list);
