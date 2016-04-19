/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './host-summary.route';
import controller from './host-summary.controller';

export default
	angular.module('jobDetail.hostSummary', [])
		.controller('HostSummaryController', controller)
		.run(['$stateExtender', function($stateExtender){
			$stateExtender.addState(route);
		}]);