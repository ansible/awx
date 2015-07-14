/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './add.route';
import controller from './add.controller';

export default
    angular.module('inventoryScriptsAdd', [])
        .controller('addController', controller)
        .config(['$routeProvider', function($routeProvider) {
            var url = route.route;
            delete route.route;
            $routeProvider.when(url, route);
        }]);
