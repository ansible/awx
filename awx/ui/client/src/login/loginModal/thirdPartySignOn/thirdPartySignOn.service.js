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
    ['$http', '$log', 'i18n', function($http, $log, i18n) {
        return function (params) {
            var url = params.url;

                return $http({
                    method: 'GET',
                    url: url,
                }).then(function (data) {
                    var options = [],
                        error = "";

                    function parseAzure(option) {
                        var newOption = {};

                        newOption.type = "azure";
                        newOption.icon = "ThirdPartySignOn-icon--fontCustom icon-microsoft";
                        newOption.link = option.login_url;
                        newOption.tooltip = i18n.sprintf(i18n._("Sign in with %s"), "Azure AD");

                        return newOption;
                    }

                    function parseGoogle(option) {
                        var newOption = {};

                        newOption.type = "google";
                        newOption.icon = "ThirdPartySignOn-icon--fontCustom icon-google";
                        newOption.link = option.login_url;
                        newOption.tooltip = i18n.sprintf(i18n._("Sign in with %s"), "Google");

                        return newOption;
                    }

                    function parseGithub(option, key) {
                        var newOption = {};

                        newOption.type = "github";
                        newOption.icon = "fa-github ThirdPartySignOn-icon--gitHub";
                        newOption.link = option.login_url;
                        newOption.tooltip = i18n.sprintf(i18n._("Sign in with %s"), "GitHub");

                        // if this is a GitHub team or org, add that to
                        // the tooltip
                        if (key.split("-")[1]){
                            if (key.split("-")[1] === "team") {
                                newOption.tooltip = i18n.sprintf(i18n._("Sign in with %s Teams"), "GitHub");
                            } else if (key.split("-")[1] === "org") {
                                newOption.tooltip = i18n.sprintf(i18n._("Sign in with %s Organizations"), "GitHub");
                            }
                        }

                        return newOption;
                    }

                    function parseSaml(option, key) {
                        var newOption = {};

                        newOption.type = "saml";
                        newOption.icon = "ThirdPartySignOn-icon--fontCustom icon-saml-02";
                        newOption.link = option.login_url;
                        newOption.tooltip = i18n.sprintf(i18n._("Sign in with %s"), "SAML");

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
                        if (key.split("-")[0] === "azuread") {
                            finalOption = parseAzure(option, key);
                        } else if (key.split("-")[0] === "google") {
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
                    $log.error('Failed to get third-party login types.  Returned status: ' + data.status );
                });
        };
    }];
