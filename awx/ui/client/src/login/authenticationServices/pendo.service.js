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
                var tower_version = config.version.split('-')[0],
                options = {
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
                      trial: config.trial,
                      tower_version: tower_version,
                      ansible_version: config.ansible_version
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
                        deferred.reject('Could not resolve pendo role.');
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
                        config = response.data.license_info;
                        config.analytics_status = response.data.analytics_status;
                        config.version = response.data.version;
                        config.ansible_version = response.data.ansible_version;
                        if(config.analytics_status === 'detailed' || config.analytics_status === 'anonymous'){
                            $pendolytics.bootstrap();
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
                        deferred.reject('Could not resolve pendo config.');
                    });
                }
                else if(config.analytics_status === 'detailed' || config.analytics_status === 'anonymous'){
                    $pendolytics.bootstrap();
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
                        $log.debug('Pendo status is '+ config.analytics_status + '. Object below:');
                        $log.debug(options);
                        $pendolytics.identify(options);
                    }, function(reason){
                        // reject function for setRole
                        $log.debug(reason);
                    });
                }, function(reason){
                    // reject function for getConfig
                    $log.debug(reason);
                });
             }
        };
   }
];
