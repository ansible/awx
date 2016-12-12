/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$rootScope', 'GetBasePath', 'ProcessErrors', '$q', '$http', 'Rest',
    function($rootScope, GetBasePath, ProcessErrors, $q, $http, Rest) {
        var url = GetBasePath('settings');

        return {
            getConfigurationOptions: function() {
                var deferred = $q.defer();
                var returnData;

                Rest.setUrl(url + '/all');
                Rest.options()
                    .success(function(data) {
                        if($rootScope.user_is_superuser) {
                            returnData = data.actions.PUT;
                        } else {
                            returnData = data.actions.GET;
                        }

                        //LICENSE is read only, returning here explicitly for display
                        // Removing LICENSE display until 3.2 or later
                        //returnData.LICENSE = data.actions.GET.LICENSE;
                        deferred.resolve(returnData);
                    })
                    .error(function(error) {
                        deferred.reject(error);
                    });

                return deferred.promise;
            },

            patchConfiguration: function(body) {
                var deferred = $q.defer();

                Rest.setUrl(url + 'all');
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
                Rest.setUrl(url + '/all');
                Rest.get()
                    .success(function(data) {
                        deferred.resolve(data);
                    })
                    .error(function(error) {
                        deferred.reject(error);
                    });

                return deferred.promise;
            },

            resetAll: function() {
                var deferred = $q.defer();

                Rest.setUrl(url + '/all');
                Rest.destroy()
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
