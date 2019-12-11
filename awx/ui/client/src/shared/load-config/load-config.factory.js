export default
    function LoadConfig($rootScope, Store, ConfigSettings) {
        return function() {

            var configSettings = {};

            if(ConfigSettings.custom_logo) {
                configSettings.custom_logo = true;
                $rootScope.custom_logo = ConfigSettings.custom_logo;
            } else {
                configSettings.custom_logo = false;
            }

            if(ConfigSettings.custom_login_info) {
                configSettings.custom_login_info = ConfigSettings.custom_login_info;
                $rootScope.custom_login_info = ConfigSettings.custom_login_info;
            } else {
                configSettings.custom_login_info = false;
            }

            if (ConfigSettings.login_redirect_override) {
                configSettings.login_redirect_override = ConfigSettings.login_redirect_override;
            }

            // Auto-resolving what used to be found when attempting to load local_setting.json
            if ($rootScope.loginConfig) {
                $rootScope.loginConfig.resolve('config loaded');
            }
            global.$AnsibleConfig = configSettings;
            Store('AnsibleConfig', global.$AnsibleConfig);
            $rootScope.$emit('ConfigReady');

            // Load new hardcoded settings from above
            $rootScope.$emit('LoadConfig');

        };
    }

LoadConfig.$inject =
    [ '$rootScope', 'Store', 'ConfigSettings' ];
