/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'jobDetail.host-summary',
    url: '/event-summary',
    socket: {
        "groups":{
            "jobs": ["status_changed"]
        }
    },
    socket: {
        "groups":{
            "jobs": ["status_changed", "summary"],
            "job_events": []
        }
    },
    views:{
        'host-summary': {
            controller: 'HostSummaryController',
            templateUrl: templateUrl('job-detail/host-summary/host-summary'),
        }
    },
    ncyBreadcrumb: {
        skip: true // Never display this state in breadcrumb.
    }
};
