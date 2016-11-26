/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import rbacMultiselectList from './rbac-multiselect-list.directive';
import rbacMultiselectRole from './rbac-multiselect-role.directive';
import teamsList from './permissionsTeams.list';
import usersList from './permissionsUsers.list';

export default
    angular.module('rbacMultiselectModule', [])
        .directive('rbacMultiselectList', rbacMultiselectList)
        .directive('rbacMultiselectRole', rbacMultiselectRole)
        .factory('addPermissionsTeamsList', teamsList)
        .factory('addPermissionsUsersList', usersList);
