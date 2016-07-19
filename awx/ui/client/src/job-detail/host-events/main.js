/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './host-events.route';
import controller from './host-events.controller';

export default
	angular.module('jobDetail.hostEvents', [])
		.controller('HostEventsController', controller)
		.run(['$stateExtender', function($stateExtender){
			$stateExtender.addState(route);
		}]);
