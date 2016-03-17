/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './organizations-edit.route';
import controller from './organizations-edit.controller';

export default
    angular.module('organizationsEdit', [])
        .controller('organizationsEditController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
