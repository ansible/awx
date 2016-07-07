/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'jobTemplates.edit',
    url: '/:template_id',
    templateUrl: templateUrl('job-templates/edit/job-templates-edit'),
    controller: 'JobTemplatesEdit',
    data: {
        activityStreamId: 'template_id'
    },
    params: {
        copied: null
    }
};
