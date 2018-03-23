/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { templateUrl } from '../../shared/template-url/template-url.factory';

export default {
    name: 'adHocJobStdout',
    route: '/ad_hoc_commands/:id',
    templateUrl: templateUrl('standard-out/adhoc/standard-out-adhoc'),
    controller: 'JobStdoutController',
    ncyBreadcrumb: {
        parent: "jobs",
        label: "{{ job.module_name }}"
    },
    data: {
        jobType: 'ad_hoc_commands',
        socket: {
            "groups": {
                "jobs": ["status_changed", "summary"],
                "ad_hoc_command_events": []
            }
        }
    },
    resolve: {
        jobData: ['Rest', 'GetBasePath', '$stateParams', function(Rest, GetBasePath, $stateParams) {
            Rest.setUrl(GetBasePath('base') + 'ad_hoc_commands/' + $stateParams.id + '/');
            return Rest.get()
                .then(({data}) => {
                    return data;
                });
        }]
    }
};
