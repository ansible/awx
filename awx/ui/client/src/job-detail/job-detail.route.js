/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'jobDetail',
    url: '/jobs/:id',
    ncyBreadcrumb: {
        parent: 'jobs',
        label: "{{ job.id }} - {{ job.name }}"
    },
    socket: {
        "groups":{
            "jobs": ["status_changed", "summary"]
            // "job_events": `[${stateParams.id}]`
        }
    },
    templateUrl: templateUrl('job-detail/job-detail'),
    controller: 'JobDetailController'
};
