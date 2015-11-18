/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */

import thirdPartySignOnController from './thirdPartySignOn.controller';

export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: true,
                controller: thirdPartySignOnController,
                templateUrl: templateUrl('login/loginModal/thirdPartySignOn/thirdPartySignOn'),
                link: function(scope, element, attrs) {
                }
            };
        }
    ];
