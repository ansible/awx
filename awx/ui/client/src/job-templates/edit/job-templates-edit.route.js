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
    socket:{
        "groups":{
            "jobs": ["status_changed"]
        }
    },
    ncyBreadcrumb: {
        parent: 'jobTemplates',
        label: "{{name}}"
    },
    onExit: function(){
        // close the survey maker modal
        // using an onExit event to handle cases where the user navs away using the url bar / back and not modal "X"

        if($("#survey-modal-dialog").hasClass('ui-dialog-content')) {
            $('#survey-modal-dialog').dialog('destroy');
        }
    }
};
