/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobsList from './jobs-list.controller';
import jobsRoute from './jobs.route';
import DeleteJob from './factories/delete-job.factory';
import JobStatusToolTip from './factories/job-status-tool-tip.factory';
import JobsListUpdate from './factories/jobs-list-update.factory';
import RelaunchAdhoc from './factories/relaunch-adhoc.factory';
import RelaunchInventory from './factories/relaunch-inventory.factory';
import RelaunchJob from './factories/relaunch-job.factory';
import RelaunchPlaybook from './factories/relaunch-playbook.factory';
import RelaunchSCM from './factories/relaunch-scm.factory';
import AllJobsList from './all-jobs.list';

export default
    angular.module('JobsModule', [])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(jobsRoute);
        }])
        .controller('JobsList', jobsList)
        .factory('DeleteJob', DeleteJob)
        .factory('JobStatusToolTip', JobStatusToolTip)
        .factory('JobsListUpdate', JobsListUpdate)
        .factory('RelaunchAdhoc', RelaunchAdhoc)
        .factory('RelaunchInventory', RelaunchInventory)
        .factory('RelaunchJob', RelaunchJob)
        .factory('RelaunchPlaybook', RelaunchPlaybook)
        .factory('RelaunchSCM', RelaunchSCM)
        .factory('AllJobsList', AllJobsList);
