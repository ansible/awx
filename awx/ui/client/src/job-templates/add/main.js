/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobTemplateAddRoute from './job-templates-add.route';
import inventoryJobTemplateAddRoute from './inventory-job-templates-add.route';
import controller from './job-templates-add.controller';

export default
    angular.module('jobTemplatesAdd', [])
        .controller('JobTemplatesAdd', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(jobTemplateAddRoute);
            $stateExtender.addState(inventoryJobTemplateAddRoute);
        }]);
