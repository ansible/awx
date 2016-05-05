/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './inventory-add.route';

export default
    angular.module('inventoryAdd', [])
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
