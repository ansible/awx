/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */
export default
    [   'templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: true,
                // controller: authenticationController,
                templateUrl: templateUrl('login/loginModal/thirdPartySignOn/thirdPartySignOn'),
                link: function(scope, element, attrs) {
                    // these vars will be set programatically once
                    // api stuff lands
                    scope.loginItems = [
                        {
                            type: "foo",
                            icon: "fa-github",
                            link: "https://google.com",
                            tooltip: "Login in via Google"
                        },
                        {
                            type: "foo",
                            icon: "fa-github",
                            link: "https://google.com",
                            tooltip: "Login in via Github"
                        },
                        {
                            type: "foo",
                            icon: "fa-github",
                            link: "https://google.com",
                            tooltip: "Login in via SAML"
                        }
                    ]

                    scope.thirdPartyLoginSupported = true;
                }
            };
        }
    ];
