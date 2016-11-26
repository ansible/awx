/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import addRbacUserTeamDirective from './rbac-user-team.directive';
import rbacMultiselect from '../rbac-multiselect/main';

export default
    angular.module('AddRbacUserTeamModule', [rbacMultiselect.name])
        .directive('addRbacUserTeam', addRbacUserTeamDirective);
