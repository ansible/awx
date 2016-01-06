/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import userRoute from './user-add.route';
import teamRoute from './team-add.route';
import controller from './add.controller';

export default
    angular.module('permissionsAdd', [])
        .controller('permissionsAddController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(userRoute);
            $stateExtender.addState(teamRoute);
        }]);
