/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobTemplateEditRoute from './job-templates-edit.route';
import inventoryJobTemplateEditRoute from './inventory-job-templates-edit.route';
import controller from './job-templates-edit.controller';

export default
    angular.module('jobTemplatesEdit', [])
        .controller('JobTemplatesEdit', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(jobTemplateEditRoute);
            $stateExtender.addState(inventoryJobTemplateEditRoute);
        }]);
