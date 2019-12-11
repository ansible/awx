export default
    function LoadConfig($rootScope, Store) {
        return function() {

            var configSettings = {};

            if(global.$ConfigResponse.custom_logo) {
                configSettings.custom_logo = true;
                $rootScope.custom_logo = global.$ConfigResponse.custom_logo;
            } else {
                configSettings.custom_logo = false;
            }

            if(global.$ConfigResponse.custom_login_info) {
                configSettings.custom_login_info = global.$ConfigResponse.custom_login_info;
                $rootScope.custom_login_info = global.$ConfigResponse.custom_login_info;
            } else {
                configSettings.custom_login_info = false;
            }

            if (global.$ConfigResponse.login_redirect_override) {
                configSettings.login_redirect_override = global.$ConfigResponse.login_redirect_override;
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
    [ '$rootScope', 'Store' ];
