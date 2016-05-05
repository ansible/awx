/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import controller from './job-templates-copy.controller';
import route from './job-templates-copy.route';
import service from './job-templates-copy.service';

export default
 	angular.module('jobTemplates.copy', [])
 		.service('jobTemplateCopyService', service)
 		.controller('jobTemplateCopyController', controller)
 		.run(['$stateExtender', function($stateExtender) {
 			$stateExtender.addState(route);
 		}]);
