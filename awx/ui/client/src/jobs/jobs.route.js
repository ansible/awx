/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import { N_ } from '../i18n';
 import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    searchPrefix: 'job',
    name: 'jobs',
    url: '/jobs',
    ncyBreadcrumb: {
        label: N_("JOBS")
    },
    params: {
        job_search: {
            value: {
                not__launch_type: 'sync',
                order_by: '-finished'
            },
            dynamic: true,
            squash: ''
        }
    },
    data: {
        socket: {
            "groups": {
                "jobs": ["status_changed"],
                "schedules": ["changed"]
            }
        }
    },
    resolve: {
        Dataset: ['AllJobsList', 'QuerySet', '$stateParams', 'GetBasePath', (list, qs, $stateParams, GetBasePath) => {
            let path = GetBasePath(list.basePath) || GetBasePath(list.name);
            return qs.search(path, $stateParams[`${list.iterator}_search`]);
        }],
        ListDefinition: ['AllJobsList', (list) => {
            return list;
        }]
    },
    views: {
        '@': {
            templateUrl: templateUrl('jobs/jobs')
        },
        'list@jobs': {
            templateProvider: function(AllJobsList, generateList) {
                let html = generateList.build({
                    list: AllJobsList,
                    mode: 'edit'
                });
                return html;
            },
            controller: 'JobsList'
        }
    }
};
