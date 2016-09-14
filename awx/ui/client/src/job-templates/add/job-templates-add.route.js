/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'jobTemplates.add',
    url: '/add',
    templateUrl: templateUrl('job-templates/add/job-templates-add'),
    controller: 'JobTemplatesAdd',
    ncyBreadcrumb: {
        parent: "jobTemplates",
        label: "CREATE JOB TEMPLATE"
    },
    socket:{
        "groups":{
            "jobs": ["status_changed"]
        }
    },
    onExit: function(){
        // close the survey maker modal
        // using an onExit event to handle cases where the user navs away using the url bar / back and not modal "X"

        if($("#survey-modal-dialog").hasClass('ui-dialog-content')) {
            $('#survey-modal-dialog').dialog('destroy');
        }
    }
};
