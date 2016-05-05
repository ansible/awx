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
    }
};
