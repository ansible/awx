/*************************************************
* Copyright (c) 2016 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default
   [ '$rootScope', '$pendolytics', 'Rest', 'GetBasePath', 'ProcessErrors', '$q',
   function ($rootScope, $pendolytics, Rest, GetBasePath, ProcessErrors, $q) {
       return {
            get: function(){
                return this.config;
            },

            set: function(config){
                this.config = config;
            },

            getConfig: function () {
                var config = this.get(),
                that = this,
                deferred = $q.defer();
                if(_.isEmpty(config)){
                    var url = GetBasePath('config');
                    Rest.setUrl(url);
                    var promise = Rest.get();
                    promise.then(function (response) {
                        var config = response.data;
                        that.set(config);
                        deferred.resolve(response.data);
                    });
                    promise.catch(function (response) {
                        ProcessErrors($rootScope, response.data, response.status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get inventory name. GET returned status: ' +
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
            }
        };
   }
];
