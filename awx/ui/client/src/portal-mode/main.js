/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import route from './portal-mode.route';
import templatesRoute from '~features/templates/routes/portalModeTemplatesList.route.js';
import myJobsRoute from '~features/jobs/routes/portalModeMyJobs.route.js';
import allJobsRoute from '~features/jobs/routes/portalModeAllJobs.route.js';
export default
 	angular.module('portalMode', [])
 		.run(['$stateExtender', function($stateExtender){
        $stateExtender.addState(templatesRoute);
        $stateExtender.addState(myJobsRoute);
        $stateExtender.addState(allJobsRoute);
 		}]);
