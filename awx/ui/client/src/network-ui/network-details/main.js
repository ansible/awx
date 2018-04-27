/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import awxNetDetailsPanel from './details.directive';

export default
    angular.module('networkDetailsDirective', [])
        .directive('awxNetDetailsPanel', awxNetDetailsPanel);
