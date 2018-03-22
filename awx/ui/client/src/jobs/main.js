/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobsList from './jobs-list.controller';
import DeleteJob from './factories/delete-job.factory';
import AllJobsList from './all-jobs.list';

export default
    angular.module('JobsModule', [])
        .controller('JobsList', jobsList)
        .factory('DeleteJob', DeleteJob)
        .factory('AllJobsList', AllJobsList);
