/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './copy.route';

export default
angular.module('inventory-copy', [])
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(route.copy);
        $stateExtender.addState(route.copyGroup);
        $stateExtender.addState(route.copyHost);
    }]);
