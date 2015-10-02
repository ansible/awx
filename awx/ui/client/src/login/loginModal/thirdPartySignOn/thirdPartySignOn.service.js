/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

    /**
 * @ngdoc function
 * @name helpers.function:Permissions
 * @description
 *  Gets the configured auth types based on the configurations set in the server
 *
 */

 export default
    ['$http', 'ProcessErrors', function($http, ProcessErrors) {
        return function (params) {
            var scope = params.scope,
                url = params.url;

                return $http({
                    method: 'GET',
                    url: url,
                }).then(function (data) {
                    var options = [],
                        error = "";

                    function parseGoogle(option, key) {
                        var newOption = {};

                        newOption.type = "google";
                        newOption.icon = "ThirdPartySignOn-icon--fontCustom icon-google";
                        newOption.link = option.login_url;
                        newOption.tooltip = "Sign in with Google";

                        return newOption;
                    }

                    function parseGithub(option, key) {
                        var newOption = {};

                        newOption.type = "github";
                        newOption.icon = "fa-github";
                        newOption.link = option.login_url;
                        newOption.tooltip = "Sign in with GitHub";

                        // if this is a GitHub team or org, add that to
                        // the tooltip
                        if (key.split("-")[1]){
                            if (key.split("-")[1] === "team") {
                                newOption.tooltip += " Teams";
                            } else if (key.split("-")[1] === "org") {
                                newOption.tooltip += " Organizations";
                            }
                        }

                        return newOption;
                    }

                    function parseSaml(option, key) {
                        var newOption = {};

                        newOption.type = "saml";
                        newOption.icon = "ThirdPartySignOn-icon--fontCustom icon-saml-02";
                        newOption.link = option.login_url;
                        newOption.tooltip = "Sign in with SAML";

                        // add the idp of the saml type to the tooltip
                        if (key.split(":")[1]){
                            newOption.tooltip += " (" + key.split(":")[1] + ")";
                        }

                        return newOption;
                    }

                    function parseLoginOption(option, key) {
                        var finalOption;

                        // set up the particular tooltip, icon, etc.
                        // needed by the login type
                        if (key.split("-")[0] === "google") {
                            finalOption = parseGoogle(option, key);
                        } else if (key.split("-")[0] === "github") {
                            finalOption = parseGithub(option, key);
                        } else if (key.split(":")[0] === "saml") {
                            finalOption = parseSaml(option, key);
                        }

                        // set the button to error red and set the error message to be passed to the login modal.
                        if (option.error) {
                            finalOption.button = "ThirdPartySignOn-button--error";
                            error = option.error;
                        }

                        options.push(finalOption);
                    }

                    // iterate over each login option passed from the API
                    _.forEach(data.data, parseLoginOption);

                    // return the options and the error to be utilized
                    // by the loginModal
                    return {"options": options, "error": error};
                })
                .catch(function (data) {
                    ProcessErrors(scope, data.data, data.status, null, { hdr: 'Error!',
                            msg: 'Failed to get third-party login types.  Returned status: ' + data.status });
                });
        };
    }];
