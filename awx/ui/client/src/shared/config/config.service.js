/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default
   ['GetBasePath', 'ProcessErrors', '$q', 'Rest', '$rootScope', 'Wait',
   function (GetBasePath, ProcessErrors, $q, Rest, $rootScope, Wait) {
       return {
            get: function(){
                return this.config;
            },

            set: function(config){
                this.config = config;
            },

            delete: function(){
                delete(this.config);
            },

            getConfig: function (licenseInfo) {
                var config = this.get(),
                that = this,
                deferred = $q.defer();
                if(_.isEmpty(config)){
                    var url = GetBasePath('config');
                    Rest.setUrl(url);
                    Wait('start');
                    var promise = Rest.get();
                    promise.then(function (response) {
                        // if applicable, use the license POSTs response if the config GET request is not returned due to a
                        // cluster cache update race condition
                        if (_.isEmpty(response.data.license_info) && !_.isEmpty(licenseInfo)) {
                            response.data.license_info = licenseInfo;
                        }
                        var config = response.data;
                        $rootScope.configReady = true;
                        Wait('stop');
                        that.set(config);
                        deferred.resolve(response.data);
                    });
                    promise.catch(function (response) {
                        ProcessErrors($rootScope, response.data, response.status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get config. GET returned status: ' +
                            response.status });
                        deferred.reject('Could not resolve pendo config.');
                    });
                }
                else if(config){
                    this.set(config);
                    deferred.resolve(config);
                }
                else {
                    deferred.reject('Config not found.');
                }
                return deferred.promise;
            },

            getSubscriptions: function(username, password) {
                Rest.setUrl(`${GetBasePath('config')}subscriptions`);
                return Rest.post({ subscriptions_username: username, subscriptions_password: password} );
            }
        };
   }
];
