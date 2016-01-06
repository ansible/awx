/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './add.route';
import controller from './add.controller';

export default
    angular.module('inventoryScriptsAdd', [])
        .controller('inventoryScriptsAddController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
