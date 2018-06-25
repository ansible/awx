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
    [ '$rootScope', '$q', '$injector', '$cookies',
        function ($rootScope, $q, $injector, $cookies) {
            return {
                request: function (config) {
                    config.headers['X-Requested-With'] = 'XMLHttpRequest';
                    if (['GET', 'HEAD', 'OPTIONS'].indexOf(config.method)===-1) {
                        config.headers['X-CSRFToken'] = $cookies.get('csrftoken');
                    }
                    return config;
                },
                response: function(config) {
                    if(config.headers('Session-Timeout') !== null){
                        $rootScope.loginConfig.promise.then(function () {
                            $AnsibleConfig.session_timeout = Number(config.headers('Session-Timeout'));
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
