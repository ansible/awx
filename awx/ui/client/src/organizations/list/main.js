/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './organizations-list.route';
import controller from './organizations-list.controller';

export default
    angular.module('organizationsList', [])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
