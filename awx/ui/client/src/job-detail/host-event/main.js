/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import {hostEventModal, hostEventDetails,
  hostEventJson, hostEventStdout, hostEventStderr} from './host-event.route';
 import controller from './host-event.controller';

 export default
 	angular.module('jobDetail.hostEvent', [])
 		.controller('HostEventController', controller)

 		.run(['$stateExtender', function($stateExtender){
 			$stateExtender.addState(hostEventModal);
 			$stateExtender.addState(hostEventDetails);
 			$stateExtender.addState(hostEventJson);
 			$stateExtender.addState(hostEventStdout);
 			$stateExtender.addState(hostEventStderr);
 		}]);
