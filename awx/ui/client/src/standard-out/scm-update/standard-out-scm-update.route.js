/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

// TODO: figure out what this route should be - should it be scm_update?

export default {
    name: 'scmUpdateStdout',
    route: '/scm_update/:id',
    templateUrl: templateUrl('standard-out/scm-update/standard-out-scm-update'),
    controller: 'JobStdoutController',
    ncyBreadcrumb: {
        parent: "jobs",
        label: "{{ project_name }}"
    },
    socket: {
        "groups":{
            "jobs": ["status_changed"]
        }
    },
    data: {
        jobType: 'project_updates'
    }
};
