/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import {hostEventModal,
  hostEventJson, hostEventStdout, hostEventStderr} from './host-event.route';
 import controller from './host-event.controller';

 export default
 	angular.module('jobResults.hostEvent', [])
 		.controller('HostEventController', controller)

 		.run(['$stateExtender', function($stateExtender){
 			$stateExtender.addState(hostEventModal);
 			$stateExtender.addState(hostEventJson);
 			$stateExtender.addState(hostEventStdout);
 			$stateExtender.addState(hostEventStderr);
 		}]);
