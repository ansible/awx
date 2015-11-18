/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import deleteJobTemplate from './delete-job-template.service';
import surveyMaker from './survey-maker/main';

export default
    angular.module('jobTemplates',
                   [    surveyMaker.name
                   ])
        .service('deleteJobTemplate', deleteJobTemplate);
