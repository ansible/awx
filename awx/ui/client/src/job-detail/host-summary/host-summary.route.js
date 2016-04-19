/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'jobDetail.host-summary',
    resolve: {
        jobSocket: ['Socket', '$rootScope', function(Socket, $rootScope) {
            var job_socket = Socket({
                    scope: $rootScope,
                    endpoint: "jobs"
            });
            job_socket.init();
            return job_socket;
        }]
    },
    views:{
        'host-summary': {
            controller: 'HostSummaryController',
            templateUrl: templateUrl('job-detail/host-summary/host-summary'),
        }
    }
};
