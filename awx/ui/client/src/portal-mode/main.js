/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './portal-mode.route';
import myJobsRoute from './jobs/portal-mode-my-jobs.route';
import allJobsRoute from './jobs/portal-mode-all-jobs.route';
import PortalJobsList from './portal-jobs.list';
import PortalJobTemplateList from './portal-job-templates.list';

export default
 	angular.module('portalMode', [])
    .factory('PortalJobsList', PortalJobsList)
    .factory('PortalJobTemplateList', PortalJobTemplateList)
 		.run(['$stateExtender', function($stateExtender){
 			$stateExtender.addState(route);
            $stateExtender.addState(myJobsRoute);
            $stateExtender.addState(allJobsRoute);
 		}]);
