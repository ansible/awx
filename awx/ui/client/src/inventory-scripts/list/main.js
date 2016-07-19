/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './list.route';
import controller from './list.controller';

export default
    angular.module('inventoryScriptsList', [])
        .controller('inventoryScriptsListController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
