/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import addUsersDirective from './addUsers.directive';

export default
    angular.module('AddUsers', [])
        .directive('addUsers', addUsersDirective);
