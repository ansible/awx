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
    resolve: {
        jobEventsSocket: ['Socket', '$rootScope', function(Socket, $rootScope) {
            if (!$rootScope.event_socket) {
                $rootScope.event_socket = Socket({
                    scope: $rootScope,
                    endpoint: "job_events"
                });
                $rootScope.event_socket.init();
                // returns should really be providing $rootScope.event_socket
                // otherwise, we have to inject the entire $rootScope into the controller
                return true;
            } else {
                return true;
            }
        }]
    },
    templateUrl: templateUrl('job-detail/job-detail'),
    controller: 'JobDetailController',
    onExit: function(){
        // close the job launch modal
        // using an onExit event to handle cases where the user navs away using the url bar / back and not modal "X"
        // Destroy the dialog
        if($("#job-launch-modal").hasClass('ui-dialog-content')) {
            $('#job-launch-modal').dialog('destroy');
        }
        // Remove the directive from the page (if it's there)
        $('#content-container').find('submit-job').remove();
    }
};
