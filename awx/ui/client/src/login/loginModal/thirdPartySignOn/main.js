/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import thirdPartySignOnDirective from './thirdPartySignOn.directive';

export default
    angular.module('thirdPartySignOn', [])
        .directive('thirdPartySignOn', thirdPartySignOnDirective);
