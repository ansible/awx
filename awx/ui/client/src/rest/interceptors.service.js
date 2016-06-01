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
    [ '$rootScope', '$q', '$injector',
        function ($rootScope, $q, $injector) {
            return {
                response: function(config) {
                    if(config.headers('auth-token-timeout') !== null){
                        $rootScope.loginConfig.promise.then(function () {
                            $AnsibleConfig.session_timeout = Number(config.headers('auth-token-timeout'));
                        });
                    }
                    return config;
                },
                responseError: function(rejection){
                    if(rejection && rejection.data && rejection.data.detail && rejection.data.detail === "Maximum per-user sessions reached"){
                        $rootScope.sessionTimer.expireSession('session_limit');
                        var state = $injector.get('$state');
                        state.go('signOut');
                        return $q.reject(rejection);
                    }
                    return $q.reject(rejection);
                }
            };
 }];
