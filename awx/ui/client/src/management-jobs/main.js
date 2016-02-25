/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import managementJobsCard from './card/main';
import managementJobsScheduler from './scheduler/main';
import list from './management-jobs.list';

export default
    angular.module('managementJobs', [
        managementJobsCard.name,
        managementJobsScheduler.name
    ])
    .factory('managementJobsListObject', list);
