/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './portal-mode.route';
import PortalJobsList from './portal-jobs.list';
import PortalJobTemplateList from './portal-job-templates.list';

export default
 	angular.module('portalMode', [])
    .factory('PortalJobsList', PortalJobsList)
    .factory('PortalJobTemplateList', PortalJobTemplateList)
 		.run(['$stateExtender', function($stateExtender){
 			$stateExtender.addState(route);
 		}]);
