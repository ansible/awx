/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import userRoute from './user-edit.route';
import teamRoute from './team-edit.route';
import controller from './edit.controller';

export default
    angular.module('permissionsEdit', [])
        .controller('permissionsEditController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(userRoute);
            $stateExtender.addState(teamRoute);
        }]);
