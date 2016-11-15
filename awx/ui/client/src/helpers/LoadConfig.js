/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

    /**
 * @ngdoc function
 * @name helpers.function:LoadConfig
 * @description   Attempts to load local_config.js. If not found, loads config.js. Then evaluates the loaded
 *  javascript, putting the result in $AnsibleConfig.
 *  LoadConfigHelper
 *
 *
 *
 */

/*jshint evil:true */



export default
angular.module('LoadConfigHelper', ['Utilities'])

.factory('LoadConfig', ['$log', '$rootScope', '$http', '$location',
    'ProcessErrors', 'Store',
    function($log, $rootScope, $http, $location, ProcessErrors, Store) {
        return function() {

            // These ettings used to be found in config.js, hardcoded now.
            var configSettings = {
                // custom_logo: true, // load /var/lib/awx/public/static/assets/custom_console_logo.png as the login modal header.  if false, will load the standard tower console logo
                // custom_login_info: "example notice", // have a notice displayed in the login modal for users.  note that, as a security measure, custom html is not supported and will be escaped.
                "tooltip_delay": {
                    "show": 500,
                    "hide": 100
                },
                "password_length": 8,
                "password_hasLowercase": true,
                "password_hasUppercase": false,
                "password_hasNumber": true,
                "password_hasSymbol": false,
                "variable_edit_modes": {
                    "yaml": {
                        "mode": "text/x-yaml",
                        "matchBrackets": true,
                        "autoCloseBrackets": true,
                        "styleActiveLine": true,
                        "lineNumbers": true,
                        "gutters": ["CodeMirror-lint-markers"],
                        "lint": true
                    },
                    "json": {
                        "mode": "application/json",
                        "styleActiveLine": true,
                        "matchBrackets": true,
                        "autoCloseBrackets": true,
                        "lineNumbers": true,
                        "gutters": ["CodeMirror-lint-markers"],
                        "lint": true
                    }
                },
            };

            // Auto-resolving what used to be found when attempting to load local_setting.json
            if ($rootScope.loginConfig) {
                $rootScope.loginConfig.resolve('config loaded');
            }
            $rootScope.$emit('ConfigReady');

            // Load new hardcoded settings from above
            // TODO Add a check for a custom image to add to the settings.
                // Update flag to true
                // in loginModal.controller load the base64 src
                // change partial to use base65 in the img src

            global.$AnsibleConfig = configSettings;
            Store('AnsibleConfig', global.$AnsibleConfig);
            $rootScope.$emit('LoadConfig');


        };
    }
]);
