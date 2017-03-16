export default
    function LoadConfig($log, $rootScope, $http, Store) {
        return function() {

            // These ettings used to be found in config.js, hardcoded now.
            var configSettings = {
                //custom_logo: false, // load /var/lib/awx/public/static/assets/custom_console_logo.png as the login modal header.  if false, will load the standard tower console logo
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

            var configInit = function() {
                // Auto-resolving what used to be found when attempting to load local_setting.json
                if ($rootScope.loginConfig) {
                    $rootScope.loginConfig.resolve('config loaded');
                }
                $rootScope.$emit('ConfigReady');

                // Load new hardcoded settings from above

                global.$AnsibleConfig = configSettings;
                Store('AnsibleConfig', global.$AnsibleConfig);
                $rootScope.$emit('LoadConfig');
            };

            // Retrieve the custom logo information - update configSettings from above
            $http({
                method: 'GET',
                url: '/api',
            })
                .success(function(response) {
                    if(response.custom_logo) {
                        configSettings.custom_logo = true;
                        $rootScope.custom_logo = response.custom_logo;
                    } else {
                        configSettings.custom_logo = false;
                    }

                    if(response.custom_login_info) {
                        configSettings.custom_login_info = response.custom_login_info;
                        $rootScope.custom_login_info = response.custom_login_info;
                    } else {
                        configSettings.custom_login_info = false;
                    }

                    configInit();

                }).error(function(error) {
                    $log.debug(error);
                    configInit();
                });

        };
    }

LoadConfig.$inject =
    [   '$log', '$rootScope', '$http',
        'Store'
    ];
