/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import managementJobsCard from './card/main';
import managementJobsSchedule from './schedule/main';
import list from './management-jobs.list';

export default
    angular.module('managementJobs', [
        managementJobsCard.name,
        managementJobsSchedule.name
    ])
    .factory('managementJobsListObject', list);
