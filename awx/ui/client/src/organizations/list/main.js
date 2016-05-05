/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './organizations-list.route';

export default
    angular.module('organizationsList', [])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
