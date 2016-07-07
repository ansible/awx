/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'managementJobsList',
    route: '/management_jobs',
    templateUrl: templateUrl('management-jobs/card/card'),
    controller: 'managementJobsCardController',
    data: {
        activityStream: true,
        activityStreamTarget: 'management_job'
    },
    ncyBreadcrumb: {
        parent: 'setup',
        label: 'MANAGEMENT JOBS'
    },
};
