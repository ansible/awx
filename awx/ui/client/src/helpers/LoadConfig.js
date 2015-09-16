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

        if ($rootScope.removeLoadConfig) {
            $rootScope.removeLoadConfig();
        }
        $rootScope.removeLoadConfig = $rootScope.$on('LoadConfig', function() {
            $rootScope.enteredPath = $location.path();
            // Load js/local_settings.json
            $http({ method:'GET', url: $basePath + 'local_settings.json' })
                .success(function(data) {
                    $log.info('loaded local_settings.json');
                    if(angular.isObject(data)){
                        $AnsibleConfig = _.extend($AnsibleConfig, data);
                        Store('AnsibleConfig', $AnsibleConfig);
                        $rootScope.$emit('ConfigReady');
                    }
                    else {
                        $log.info('local_settings.json is not a valid object');
                        $rootScope.$emit('ConfigReady');
                    }

                })
                .error(function() {
                    //local_settings.json not found
                    $log.info('local_settings.json not found');
                    $rootScope.$emit('ConfigReady');
                });
        });


        // load config.js
        $log.info('attempting to load config.js');
        $http({ method:'GET', url: $basePath + 'config.js' })
            .success(function(data) {
                $log.info('loaded config.js');
                $AnsibleConfig = eval(data);
                Store('AnsibleConfig', $AnsibleConfig);
                $rootScope.$emit('LoadConfig');
            })
            .error(function(data, status) {
                ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                    msg: 'Failed to load ' + $basePath + '/config.js. GET status: ' + status
                });
            });
    };
}]);
