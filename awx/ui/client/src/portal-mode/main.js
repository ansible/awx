/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './portal-mode.route';

export default
 	angular.module('portalMode', [])
 		.run(['$stateExtender', function($stateExtender){
 			$stateExtender.addState(route);
 		}]);