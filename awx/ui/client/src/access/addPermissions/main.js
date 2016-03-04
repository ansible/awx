/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import addPermissionsDirective from './addPermissions.directive';
import roleSelect from './roleSelect.directive';
import teamsPermissions from './teams/main';
import usersPermissions from './users/main';

export default
    angular.module('AddPermissions', [teamsPermissions.name, usersPermissions.name])
        .directive('addPermissions', addPermissionsDirective)
        .directive('roleSelect', roleSelect);
