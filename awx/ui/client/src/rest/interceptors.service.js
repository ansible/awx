/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /*************************************************
  * Copyright (c) 2015 Ansible, Inc.
  *
  * All Rights Reserved
  *************************************************/

 export default
    ['$rootScope',
        function ($rootScope) {
            return {
                response: function(config) {
                    if(config.headers('auth-token-timeout') !== null){
                        // $rootScope.sessionTimer = Number(config.headers('auth-token-timeout'));
                        $AnsibleConfig.session_timeout = Number(config.headers('auth-token-timeout'));
                        // $rootScope.sessionTimer = Timer.init();
                    }
                    return config;
                }
            };
 }];
