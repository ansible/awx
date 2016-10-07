/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'managementJobStdout',
    route: '/management_jobs/:id',
    templateUrl: templateUrl('standard-out/management-jobs/standard-out-management-jobs'),
    controller: 'JobStdoutController',
    socket: {
        "groups":{
            "jobs": ["status_changed"]
        }
    },
    ncyBreadcrumb: {
        parent: "jobs",
        label: "{{ job.name }}"
    },
    data: {
        jobType: 'system_jobs'
    }
};
