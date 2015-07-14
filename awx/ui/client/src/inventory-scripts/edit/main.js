/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './edit.route';
import controller from './edit.controller';

export default
    angular.module('inventoryScriptsEdit', [])
        .controller('editController', controller)
        .config(['$routeProvider', function($routeProvider) {
            var url = route.route;
            delete route.route;
            $routeProvider.when(url, route);
        }]);
