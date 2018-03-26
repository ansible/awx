/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import awxNetDetailsPanel from './details.directive';
import awxNetExtraVars from './network-extra-vars/network-extra-vars.directive';

export default
    angular.module('networkDetailsDirective', [])
        .directive('awxNetDetailsPanel', awxNetDetailsPanel)
        .directive('awxNetExtraVars', awxNetExtraVars);
