/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import standardOutLog from './standard-out-log.directive';
export default
    angular.module('standardOutLogDirective', [])
        .directive('standardOutLog', standardOutLog);
