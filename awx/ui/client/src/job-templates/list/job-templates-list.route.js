/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'jobTemplates',
    url: '/job_templates',
    templateUrl: templateUrl('job-templates/list/job-templates-list'),
    controller: 'JobTemplatesList',
    data: {
        activityStream: true,
        activityStreamTarget: 'job_template'
    },
    ncyBreadcrumb: {
        label: "JOB TEMPLATES"
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
