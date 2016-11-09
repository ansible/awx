/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['GetBasePath', 'ProcessErrors', '$q', '$http', 'Rest', '$rootScope', '$timeout', 'Wait',
    function(GetBasePath, ProcessErrors, $q, $http, Rest, $rootScope, $timeout, Wait) {
        var url = GetBasePath('settings');

        return {
            getConfigurationOptions: function() {
                var deferred = $q.defer();
                Rest.setUrl(url + '/all');
                Rest.options()
                    .success(function(data) {
                        var returnData = data.actions.PUT;
                        //LICENSE is read only, returning here explicitly for display
                        returnData.LICENSE = data.actions.GET.LICENSE;
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
