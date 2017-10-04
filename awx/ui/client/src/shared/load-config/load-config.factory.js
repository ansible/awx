export default
    function LoadConfig($log, $rootScope, $http, Store) {
        return function() {


            var configSettings = {};

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
                url: '/api/',
            })
                .then(function({data}) {
                    if(data.custom_logo) {
                        configSettings.custom_logo = true;
                        $rootScope.custom_logo = data.custom_logo;
                    } else {
                        configSettings.custom_logo = false;
                    }

                    if(data.custom_login_info) {
                        configSettings.custom_login_info = data.custom_login_info;
                        $rootScope.custom_login_info = data.custom_login_info;
                    } else {
                        configSettings.custom_login_info = false;
                    }

                    configInit();

                }).catch(({error}) => {
                    $log.debug(error);
                    configInit();
                });

        };
    }

LoadConfig.$inject =
    [   '$log', '$rootScope', '$http',
        'Store'
    ];
