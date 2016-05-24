/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {ManageHostsAdd, ManageHostsEdit} from './hosts.route';

export default
    angular.module('manageHosts', [])
    	.run(['$stateExtender', '$state', function($stateExtender, $state){
    		$stateExtender.addState(ManageHostsAdd);
    		$stateExtender.addState(ManageHostsEdit);
    	}]);
