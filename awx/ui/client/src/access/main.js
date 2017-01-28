/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import roleList from './rbac-role-column/roleList.directive';
import addRbacResource from './add-rbac-resource/main';
import addRbacUserTeam from './add-rbac-user-team/main';

export default
    angular.module('RbacModule', [
    	addRbacResource.name,
    	addRbacUserTeam.name
    	])
        .directive('roleList', roleList);
