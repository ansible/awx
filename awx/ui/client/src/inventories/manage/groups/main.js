/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {ManageGroupsAdd, ManageGroupsEdit} from './groups.route';

export default
    angular.module('manageGroups', [])
    	.run(['$stateExtender', function($stateExtender){
    		$stateExtender.addState(ManageGroupsAdd);
    		$stateExtender.addState(ManageGroupsEdit);
    	}]);
