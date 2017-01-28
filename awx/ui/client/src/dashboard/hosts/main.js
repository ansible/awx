/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import list from './dashboard-hosts.list';
import form from './dashboard-hosts.form';
import listController from './dashboard-hosts-list.controller';
import editController from './dashboard-hosts-edit.controller';
import service from './dashboard-hosts.service';

export default
angular.module('dashboardHosts', [])
    .service('DashboardHostService', service)
    .factory('DashboardHostsList', list)
    .factory('DashboardHostsForm', form)
    .config(['$stateProvider', 'stateDefinitionsProvider',
        function($stateProvider, stateDefinitionsProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get();

            $stateProvider.state({
                name: 'dashboardHosts',
                url: '/home/hosts',
                lazyLoad: () => stateDefinitions.generateTree({
                    urls: {
                        list: '/home/hosts'
                    },
                    parent: 'dashboardHosts',
                    modes: ['edit'],
                    list: 'DashboardHostsList',
                    form: 'DashboardHostsForm',
                    controllers: {
                        list: listController,
                        edit: editController
                    },
                    resolve: {
                        edit: {
                            host: ['Rest', '$stateParams', 'GetBasePath',
                                function(Rest, $stateParams, GetBasePath) {
                                    let path = GetBasePath('hosts') + $stateParams.host_id;
                                    Rest.setUrl(path);
                                    return Rest.get();
                                }
                            ]
                        }
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'host'
                    },
                    ncyBreadcrumb: {
                        parent: 'dashboard',
                        label: "HOSTS"
                    },
                })
            });
        }
    ]);
