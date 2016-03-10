/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import addPermissionsListDirective from './addPermissionsList.directive';
import teamsList from './permissionsTeams.list';
import usersList from './permissionsUsers.list';

export default
    angular.module('addPermissionsListModule', [])
        .directive('addPermissionsList', addPermissionsListDirective)
        .factory('addPermissionsTeamsList', teamsList)
        .factory('addPermissionsUsersList', usersList);
