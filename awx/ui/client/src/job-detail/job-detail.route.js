/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { templateUrl } from '../shared/template-url/template-url.factory';

export default {
    name: 'jobDetail',
    url: '/jobs/{id: int}',
    ncyBreadcrumb: {
        parent: 'jobs',
        label: "{{ job.id }} - {{ job.name }}"
    },
    data: {
        socket: {
            "groups": {
                "jobs": ["status_changed", "summary"],
                "job_events": []
            }
        }
    },
    templateUrl: templateUrl('job-detail/job-detail'),
    controller: 'JobDetailController'
};
