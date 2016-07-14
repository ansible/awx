/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'jobTemplates.edit',
    url: '/:id',
    templateUrl: templateUrl('job-templates/edit/job-templates-edit'),
    controller: 'JobTemplatesEdit',
    data: {
        activityStreamId: 'id'
    },
    ncyBreadcrumb: {
        parent: 'jobTemplates',
        label: "{{name}}"
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

        if($("#survey-modal-dialog").hasClass('ui-dialog-content')) {
            $('#survey-modal-dialog').dialog('destroy');
        }
    }
};
