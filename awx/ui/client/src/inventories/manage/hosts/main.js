/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {ManageHostsAdd, ManageHostsEdit} from './hosts.route';

export default
    angular.module('manageHosts', [])
    	.run(['$stateExtender', function($stateExtender){
    		$stateExtender.addState(ManageHostsAdd);
    		$stateExtender.addState(ManageHostsEdit);
    	}]);
