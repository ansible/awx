/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 /**
 *  @ngdoc overview
 *  @name shared
 *  @description lib files
 *
 */
 /**
 *  @ngdoc function
 *  @name shared.function:api-loader
 *  @description Read /api and /api/X to discover all the base paths needed
 *  to access the primary model objects.
 *
 */



export default
angular.module('ApiLoader', ['Utilities'])

.factory('LoadBasePaths', ['$http', '$rootScope', 'Store', 'ProcessErrors',
    function ($http, $rootScope, Store, ProcessErrors) {
        return function () {

            $http({ method: 'GET', url:'/api/', headers: { 'Authorization': "" } })
                .success(function (data) {
                    var base = data.current_version;
                    $http({ method: 'GET', url:base, headers: { 'Authorization': "" } })
                        .success(function (data) {
                            data.base = base;
                            $rootScope.defaultUrls = data;
                            // tiny hack to side-step api/v1/job_events not being a visible endpoint @ GET api/v1/
                            $rootScope.defaultUrls['job_events'] = '/api/v1/job_events/';
                            Store('api', data);
                        })
                        .error(function (data, status) {
                            $rootScope.defaultUrls = {
                                status: 'error'
                            };
                            ProcessErrors(null, data, status, null, {
                                hdr: 'Error',
                                msg: 'Failed to read ' + base + '. GET status: ' + status
                            });
                        });
                })
                .error(function (data, status) {
                    $rootScope.defaultUrls = {
                        status: 'error'
                    };
                    ProcessErrors(null, data, status, null, {
                        hdr: 'Error',
                        msg: 'Failed to read /api. GET status: ' + status
                    });
                });
        };
    }
])

.factory('GetBasePath', ['$rootScope', 'Store', 'LoadBasePaths', 'Empty',
    function ($rootScope, Store, LoadBasePaths, Empty) {
        return function (set) {
            // use /api/v1/ results to construct API URLs.
            if (Empty($rootScope.defaultUrls)) {
                // browser refresh must have occurred. load from local storage
                if (Store('api')) {
                    $rootScope.defaultUrls = Store('api');
                    return $rootScope.defaultUrls[set];
                }
                return ''; //we should never get here
            }
            return $rootScope.defaultUrls[set];
        };
    }
]);
