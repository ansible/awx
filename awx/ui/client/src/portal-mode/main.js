/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './portal-mode.route';
import {PortalModeController} from './portal-mode.controller';

 export default
 	angular.module('portalMode', [])
 		.controller('PortalModeController', PortalModeController)
 		.run(['$stateExtender', function($stateExtender){
 			$stateExtender.addState(route);
 		}]);