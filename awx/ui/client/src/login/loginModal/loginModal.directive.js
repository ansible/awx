/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import authenticationController from './loginModal.controller';

/* jshint unused: vars */
export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: true,
                controller: authenticationController,
                templateUrl: templateUrl('login/loginModal/loginModal'),
                link: function(scope, element, attrs) {
                    // Display the login dialog
                    $('#login-modal').modal({
                        show: true,
                        keyboard: false,
                        backdrop: 'static'
                    });
                }
            };
        }
    ];
