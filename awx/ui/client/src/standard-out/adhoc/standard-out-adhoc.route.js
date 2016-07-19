/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

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
        jobType: 'ad_hoc_commands'
    },
    resolve: {
        adhocEventsSocket: ['Socket', '$rootScope', function(Socket, $rootScope) {
            if (!$rootScope.adhoc_event_socket) {
                $rootScope.adhoc_event_socket = Socket({
                    scope: $rootScope,
                    endpoint: "ad_hoc_command_events"
                });
                $rootScope.adhoc_event_socket.init();
                return true;
            } else {
                return true;
            }
        }]
    }
};
