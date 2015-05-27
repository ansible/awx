/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import smartStatusDirective from 'tower/smart-status/smart-status.directive';
export default
    angular.module('systemStatus', [])
        .directive('awSmartStatus', smartStatusDirective);
