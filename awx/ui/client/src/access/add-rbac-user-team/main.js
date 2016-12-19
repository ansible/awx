/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import addRbacUserTeamDirective from './rbac-user-team.directive';
import rbacSelectedList from './rbac-selected-list.directive';

export default
    angular.module('AddRbacUserTeamModule', [])
        .directive('addRbacUserTeam', addRbacUserTeamDirective)
        .directive('rbacSelectedList', rbacSelectedList);