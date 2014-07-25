/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LoadConfigHelper
 *
 *  Attempts to load local_config.js. If not found, loads config.js. Then evaluates the loaded
 *  javascript, putting the result in $AnsibleConfig.
 *
 */

/*jshint evil:true */

'use strict';

angular.module('LoadConfigHelper', ['Utilities'])

.factory('LoadConfig', ['$rootScope', '$http', 'ProcessErrors', function($rootScope, $http, ProcessErrors) {
    return function() {

        if ($rootScope.removeLoadConfig) {
            $rootScope.removeLoadConfig();
        }
        $rootScope.removeLoadConfig = $rootScope.$on('LoadConfig', function() {
            // local_config.js not found, so we'll load config.js
            $http({ method:'GET', url: $basePath + 'js/config.js' })
                .success(function(data) {
                    $AnsibleConfig = eval(data);
                })
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to load ' + $basePath + '/config.js. GET status: ' + status
                    });
                });
        });

        // Load js/local_config.js
        $http({ method:'GET', url: $basePath + 'js/local_config.js' })
            .success(function(data) {
                $AnsibleConfig = eval(data);
            })
            .error(function() {
                //local_config.js not found
                $rootScope.$emit('LoadConfig');
            });
    };
}]);