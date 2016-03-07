/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import addPermissionsDirective from './addPermissions.directive';
import roleSelect from './roleSelect.directive';
import addPermissionsList from './addPermissionsList/main';

export default
    angular.module('AddPermissions', [addPermissionsList.name])
        .directive('addPermissions', addPermissionsDirective)
        .directive('roleSelect', roleSelect);
