/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './job-templates-list.route';
import controller from './job-templates-list.controller';

export default
    angular.module('jobTemplatesList', [])
        .controller('JobTemplatesList', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
