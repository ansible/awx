/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import userRoute from './user-list.route';
import teamRoute from './team-list.route';
import controller from './list.controller';

export default
    angular.module('permissionsList', [])
        .controller('permissionsListController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(userRoute);
            $stateExtender.addState(teamRoute);
        }]);
