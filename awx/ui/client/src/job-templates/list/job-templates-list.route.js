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
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
