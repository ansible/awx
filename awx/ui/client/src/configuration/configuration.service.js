/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$rootScope', 'GetBasePath', 'ProcessErrors', '$q', '$http', 'Rest',
    function($rootScope, GetBasePath, ProcessErrors, $q, $http, Rest) {
        var url = GetBasePath('settings') + 'all';

        return {
            getConfigurationOptions: function() {
                var deferred = $q.defer();
                var returnData = {};

                Rest.setUrl(url);
                Rest.options()
                    .success(function(data) {
                        // Compare GET actions with PUT actions and flag discrepancies
                        // for disabling in the UI
                        var getActions = data.actions.GET;
                        var getKeys = _.keys(getActions);
                        var putActions = data.actions.PUT;

                        _.each(getKeys, function(key) {
                            if(putActions && putActions[key]) {
                                returnData[key] = putActions[key];
                            } else {
                                returnData[key] = _.extend(getActions[key], {
                                                        required: false,
                                                        disabled: true
                                                    });
                            }
                        });

                        deferred.resolve(returnData);
                    })
                    .error(function(error) {
                        deferred.reject(error);
                    });

                return deferred.promise;
            },

            patchConfiguration: function(body) {
                var deferred = $q.defer();

                Rest.setUrl(url);
                Rest.patch(body)
                    .success(function(data) {
                        deferred.resolve(data);
                    })
                    .error(function(error) {
                        deferred.reject(error);
                    });

                return deferred.promise;
            },

            getCurrentValues: function() {
                var deferred = $q.defer();
                Rest.setUrl(url);
                Rest.get()
                    .success(function(data) {
                        deferred.resolve(data);
                    })
                    .error(function(error) {
                        deferred.reject(error);
                    });

                return deferred.promise;
            }
        };
    }
];
