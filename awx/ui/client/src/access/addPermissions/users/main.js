/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import usersDirective from './permissionsUsers.directive';
import usersList from './permissionsUsers.list';

export default
    angular.module('PermissionsUsers', [])
        .directive('addPermissionsUsers', usersDirective)
        .factory('addPermissionsUsersList', usersList);
