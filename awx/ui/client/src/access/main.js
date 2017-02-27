/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import roleList from './rbac-role-column/roleList.directive';
import addRbacResource from './add-rbac-resource/main';
import addRbacUserTeam from './add-rbac-user-team/main';
import permissionsList from './permissions-list.controller';

export default
    angular.module('RbacModule', [
    	addRbacResource.name,
    	addRbacUserTeam.name
    	])
        .controller('PermissionsList', permissionsList)
        .directive('roleList', roleList);
