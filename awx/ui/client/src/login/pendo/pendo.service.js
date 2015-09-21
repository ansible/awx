/*************************************************
* Copyright (c) 2015 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default
   [ '$rootScope', '$pendolytics', 'Rest', 'GetBasePath', 'ProcessErrors', '$q',
        'Store', '$log',
   function ($rootScope, $pendolytics, Rest, GetBasePath, ProcessErrors, $q,
        Store, $log) {
       return {
            setPendoOptions: function (config) {
                var options = {
                    visitor: {
                      id: null,
                      role: null,
                      email: null
                    },
                    account: {
                      id: null,
                      planLevel: config.license_type,
                      planPrice: config.instance_count,
                      creationDate: config.license_date,
                      trial: config.trial
                    }
                };
                if(config.analytics_status === 'detailed'){
                    this.setDetailed(options, config);
                }
                else if(config.analytics_status === 'anonymous'){
                    this.setAnonymous(options);
                }
                return options;

            },

            setDetailed: function(options, config) {
                // Detailed mode
                    // VisitorId: username+hash of license_key
                    // AccountId: hash of license_key from license
                    // email: contact_email from license OR email from Tower account

                options.visitor.id = $rootScope.current_user.username + '@' + config.deployment_id;
                options.account.id = config.deployment_id;
                options.visitor.email = $rootScope.current_user.email;
            },

            setAnonymous: function (options) {
                //Anonymous mode
                    // VisitorId: <some hardcoded id that is the same across all anonymous>
                    // AccountId: <some hardcoded id that is the same across all anonymous>
                    // email: <blank>

                options.visitor.id = 0;
                options.account.id = "tower.ansible.com";
                options.visitor.email = "";
            },

            setRole: function(options) {
                var deferred = $q.defer();
                if($rootScope.current_user.is_superuser === true){
                    options.visitor.role = 'admin';
                    deferred.resolve(options);
                }
                else{
                    var url = GetBasePath('users') + $rootScope.current_user.id + '/admin_of_organizations/';
                    Rest.setUrl(url);
                    var promise = Rest.get();
                    promise.then(function (response) {
                        if(response.data.count > 0 ) {
                            options.visitor.role = "orgadmin";
                            deferred.resolve(options);
                        }
                        else {
                            options.visitor.role = "user";
                            deferred.resolve(options);
                        }
                    });
                    promise.catch(function (response) {
                        ProcessErrors($rootScope, response.data, response.status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get inventory name. GET returned status: ' +
                            response.status });
                    });
                }
                return deferred.promise;
            },

            getConfig: function () {
                var config = Store('license'),
                deferred = $q.defer();
                if(_.isEmpty(config)){
                    var url = GetBasePath('config');
                    Rest.setUrl(url);
                    var promise = Rest.get();
                    promise.then(function (response) {
                        config = response.license_info;
                        config.analytics_status = response.analytics_status;
                        if(config.analytics_status !== 'off'){
                            deferred.resolve(config);
                        }
                        else {
                            deferred.reject('Pendo is turned off.');
                        }
                    });
                    promise.catch(function (response) {
                        ProcessErrors($rootScope, response.data, response.status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get inventory name. GET returned status: ' +
                            response.status });
                    });
                }
                else if(config.analytics_status !== 'off'){
                    deferred.resolve(config);
                }
                else {
                    deferred.reject('Pendo is turned off.');
                }
                return deferred.promise;
            },

            issuePendoIdentity: function () {
                var that = this;
                this.getConfig().then(function(config){
                    var options = that.setPendoOptions(config);
                    that.setRole(options).then(function(options){
                        $pendolytics.identify(options);
                    });
                }, function(reason){
                    $log.debug(reason);
                });
             }
        };
   }
];
