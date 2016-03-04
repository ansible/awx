/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import teamsDirective from './permissionsTeams.directive';
import teamsList from './permissionsTeams.list';

export default
    angular.module('PermissionsTeams', [])
        .directive('addPermissionsTeams', teamsDirective)
        .factory('addPermissionsTeamsList', teamsList);
