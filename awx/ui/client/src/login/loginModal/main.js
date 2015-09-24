/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import thirdPartySignOn from './thirdPartySignOn/main';

import loginModalDirective from './loginModal.directive';

export default
    angular.module('loginModal', [thirdPartySignOn.name])
        .directive('loginModal', loginModalDirective);
