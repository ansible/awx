/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import deleteJobTemplate from './delete-job-template.service';

export default
    angular.module('jobTemplates', [])
        .service('deleteJobTemplate', deleteJobTemplate);
