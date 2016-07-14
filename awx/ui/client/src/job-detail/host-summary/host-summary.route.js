/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'jobDetail.host-summary',
    url: '/event-summary',
    views:{
        'host-summary': {
            controller: 'HostSummaryController',
            templateUrl: templateUrl('job-detail/host-summary/host-summary'),
        }
    },
    ncyBreadcrumb: {
        skip: true // Never display this state in breadcrumb.
    },
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
