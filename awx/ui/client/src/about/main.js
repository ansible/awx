/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import controller from './about.controller';
 import route from './about.route';

 export default
 	angular.module('about', [])
 		.controller('about', controller)
 		.run(['$stateExtender', function($stateExtender){
 			$stateExtender.addState(route);
 		}]);
