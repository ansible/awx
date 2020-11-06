/*************************************************
* Copyright (c) 2015 Ansible, Inc.
*
* All Rights Reserved
*************************************************/


export default ['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', '$q', 'ConfigService', '$log',
    'AppStrings',
    function ($rootScope, Rest, GetBasePath, ProcessErrors, $q, ConfigService, $log, AppStrings) {
        return {
            setPendoOptions: function (config) {
                const tower_version = config.version.split('-')[0];
                const trial = (config.trial) ? config.trial : false;
                let options = {
                    apiKey: AppStrings.get('PENDO_API_KEY'),
                    visitor: {
                        id: null,
                        role: null,
                    },
                    account: {
                        id: null,
                        planLevel: config.license_type,
                        planPrice: config.instance_count,
                        creationDate: config.license_date,
                        trial: trial,
                        tower_version: tower_version,
                        ansible_version: config.ansible_version
                    }
                };

                options.visitor.id = 0;
                options.account.id = "tower.ansible.com";

                return options;
            },

            setRole: function(options) {
                const deferred = $q.defer();

                if ($rootScope.current_user.is_superuser === true) {
                    options.visitor.role = 'admin';
                    deferred.resolve(options);
                } else {
                    Rest.setUrl(GetBasePath('users') + $rootScope.current_user.id +
                        '/admin_of_organizations/');
                    Rest.get()
                        .then(function (response) {
                            if (response.data.count > 0) {
                                options.visitor.role = "orgadmin";
                                deferred.resolve(options);
                            } else {
                                options.visitor.role = "user";
                                deferred.resolve(options);
                            }
                        })
                        .catch(function (response) {
                            ProcessErrors($rootScope, response.data, response.status, null, {
                                hdr: 'Error!',
                                msg: 'Failed to get admin of org user list. GET returned status: ' +
                                    response.status });
                            deferred.reject('Could not resolve pendo role.');
                        });
                }

                return deferred.promise;
            },

            bootstrap: function(){
                /* jshint ignore:start */
                (function(p,e,n,d,o){var v,w,x,y,z;o=p[d]=p[d]||{};o._q=[];
                v=['initialize','identify','updateOptions','pageLoad'];for(w=0,x=v.length;w<x;++w)(function(m){
                o[m]=o[m]||function(){o._q[m===v[0]?'unshift':'push']([m].concat([].slice.call(arguments,0)));};})(v[w]);
                y=e.createElement(n);y.async=!0;y.src=`https://cdn.pendo.io/agent/static/${AppStrings.get('PENDO_API_KEY')}/pendo.js`;
                z=e.getElementsByTagName(n)[0];z.parentNode.insertBefore(y,z);})(window,document,'script','pendo');
                /* jshint ignore:end */
            },

            issuePendoIdentity: function () {
                const c = ConfigService.get();

                let options;
                let config = c.license_info;

                config.analytics_status = c.analytics_status;
                config.version = c.version;
                config.ansible_version = c.ansible_version;

                if (config.analytics_status === 'detailed' ||
                    config.analytics_status === 'anonymous') {
                        this.bootstrap();
                        options = this.setPendoOptions(config);
                        this.setRole(options)
                            .then(function(options){
                                $log.debug('Pendo status is '+ config.analytics_status +
                                    '. Object below:');
                                $log.debug(options);

                                /* jshint ignore:start */
                                pendo.initialize(options);
                                /* jshint ignore:end */
                            }, function(reason){
                                // reject function for setRole
                                $log.debug(reason);
                            });
                } else {
                    $log.debug('Pendo is turned off.');
                }
            },

            updatePendoTrackingState: function(tracking_type) {
                if (tracking_type === 'off' || tracking_type === 'anonymous' ||
                    tracking_type === 'detailed') {
                        Rest.setUrl(`${GetBasePath('settings')}ui`);
                        Rest.patch({ PENDO_TRACKING_STATE: tracking_type })
                            .catch(function ({data, status}) {
                                ProcessErrors($rootScope, data, status, null, {
                                    hdr: 'Error!',
                                    msg: 'Failed to patch PENDO_TRACKING_STATE in settings: ' +
                                        status });
                            });
                } else {
                    throw new Error(`Can't update pendo tracking state in settings to
                        "${tracking_type}"`);
                }
          }
        };
    }];
