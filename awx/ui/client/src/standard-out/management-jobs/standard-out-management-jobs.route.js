/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { templateUrl } from '../../shared/template-url/template-url.factory';

export default {
    name: 'managementJobStdout',
    route: '/management_jobs/:id',
    templateUrl: templateUrl('standard-out/management-jobs/standard-out-management-jobs'),
    controller: 'JobStdoutController',
    ncyBreadcrumb: {
        parent: "jobs",
        label: "{{ job.name }}"
    },
    data: {
        jobType: 'system_jobs',
        socket: {
            "groups": {
                "jobs": ["status_changed", "summary"],
                "system_job_events": [],
            }
        }
    },
    resolve: {
        jobData: ['Rest', 'GetBasePath', '$stateParams', function(Rest, GetBasePath, $stateParams) {
            Rest.setUrl(GetBasePath('base') + 'system_jobs/' + $stateParams.id + '/');
            return Rest.get()
                .then(({data}) => {
                    return data;
                });
        }]
    }
};
