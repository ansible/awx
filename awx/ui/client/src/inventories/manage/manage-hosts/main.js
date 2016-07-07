/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {ManageHostsAdd, ManageHostsEdit} from './manage-hosts.route';
import service from './manage-hosts.service';

export default
    angular.module('manageHosts', [])
    	.service('ManageHostsService', service)
    	.run(['$stateExtender', function($stateExtender){
    		$stateExtender.addState(ManageHostsAdd);
    		$stateExtender.addState(ManageHostsEdit);
    	}]);
