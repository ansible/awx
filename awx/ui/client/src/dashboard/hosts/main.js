/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {dashboardHostsList, dashboardHostsEdit} from './dashboard-hosts.route';
import list from './dashboard-hosts.list';
import form from './dashboard-hosts.form';
import service from './dashboard-hosts.service';

export default
    angular.module('dashboardHosts', [])
    .service('DashboardHostsService', service)
    .factory('DashboardHostsList', list)
    .factory('DashboardHostsForm', form)
    .run(['$stateExtender', function($stateExtender){
    	$stateExtender.addState(dashboardHostsList);
    	$stateExtender.addState(dashboardHostsEdit);
    }]);
