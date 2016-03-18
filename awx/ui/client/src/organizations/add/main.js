/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './organizations-add.route';
import controller from './organizations-add.controller';

export default
    angular.module('organizationsAdd', [])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
