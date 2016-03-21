/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import route from './edit.route';
import controller from './edit.controller';

export default
    angular.module('notificationsEdit', [])
        .controller('notificationsEditController', controller)
        .run(['$stateExtender', function($stateExtender) {
            $stateExtender.addState(route);
        }]);
