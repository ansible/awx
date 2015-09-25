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
                templateUrl: templateUrl('login/thirdPartySignOn'),
                link: function(scope, element, attrs) {
                    // these vars will be set programatically once
                    // api stuff lands
                    scope.loginItems = [
                        {
                            type: "foo",
                            icon: "ThirdPartySignOn-icon--fontCustom icon-google",
                            link: "https://google.com",
                            tooltip: "Sign in with Google"
                        },
                        {
                            type: "foo",
                            icon: "fa-github",
                            link: "https://google.com",
                            tooltip: "Sign in with Github"
                        },
                        {
                            type: "foo",
                            icon: "ThirdPartySignOn-icon--fontCustom icon-saml-02",
                            link: "https://google.com",
                            tooltip: "Sign in with SAML"
                        }
                    ]

                    scope.thirdPartyLoginSupported = true;
                }
            };
        }
    ];
