/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * APIDefaults
 *
 *
 */
 /**
 * @ngdoc function
 * @name helpers.function:api-defaults
 * @description this could use more discussion
*/

export default
    angular.module('APIDefaults', ['RestServices', 'Utilities'])
        .factory('GetAPIDefaults', ['Alert', 'Rest', '$rootScope',
            function (Alert, Rest, $rootScope) {
                return function (key) {

                    //Reload a related collection on pagination or search change

                    var result = {}, cnt = 0, url;

                    function lookup(key) {
                        var id, result = {};
                        for (id in $rootScope.apiDefaults) {
                            if (id === key || id.iterator === key) {
                                result[id] = $rootScope.apiDefaults[id];
                                break;
                            }
                        }
                        return result;
                    }

                    function wait() {
                        if ($.isEmptyObject(result) && cnt < 5) {
                            cnt++;
                            setTimeout(1000, wait());
                        } else if (result.status === 'success') {
                            return lookup(key);
                        }
                    }

                    if ($rootScope.apiDefaults === null || $rootScope.apiDefaults === undefined) {
                        url = '/api/v1/';
                        Rest.setUrl(url);
                        Rest.get()
                            .success(function (data) {
                                var id, defaults = data;
                                for (id in defaults) {
                                    switch (id) {
                                    case 'organizations':
                                        defaults[id].iterator = 'organization';
                                        break;
                                    case 'jobs':
                                        defaults[id].iterator = 'job';
                                        break;
                                    case 'users':
                                        defaults[id].iterator = 'user';
                                        break;
                                    case 'teams':
                                        defaults[id].iterator = 'team';
                                        break;
                                    case 'hosts':
                                        defaults[id].iterator = 'host';
                                        break;
                                    case 'groups':
                                        defaults[id].iterator = 'group';
                                        break;
                                    case 'projects':
                                        defaults[id].iterator = 'project';
                                        break;
                                    case 'inventories':
                                        defaults[id].iterator = 'inventory';
                                        break;
                                    }
                                }
                                $rootScope.apiDefaults = defaults;
                                result = {
                                    status: 'success'
                                };
                            })
                            .error(function (data, status) {
                                result = {
                                    status: 'error',
                                    msg: 'Call to ' + url + ' failed. GET returned status: ' + status
                                };
                            });
                        return wait();
                    } else {
                        return lookup(key);
                    }
                };
            }
        ]);
