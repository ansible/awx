/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './portal-mode.route';
import myJobsRoute from '~features/jobs/routes/portalModeMyJobs.route.js';
import allJobsRoute from '~features/jobs/routes/portalModeAllJobs.route.js';
import PortalJobTemplateList from './portal-job-templates.list';

export default
 	angular.module('portalMode', [])
    .factory('PortalJobTemplateList', PortalJobTemplateList)
 		.run(['$stateExtender', function($stateExtender){
 			  $stateExtender.addState(route);
        $stateExtender.addState(myJobsRoute);
        $stateExtender.addState(allJobsRoute);
 		}]);
