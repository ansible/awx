/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import thirdPartySignOnDirective from './thirdPartySignOn.directive';
import thirdPartySignOnService from './thirdPartySignOn.service';

export default
    angular.module('thirdPartySignOn', [])
        .directive('thirdPartySignOn', thirdPartySignOnDirective)
        .factory('thirdPartySignOnService', thirdPartySignOnService);
