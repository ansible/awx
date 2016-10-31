/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import HostsAddController from './hosts-add.controller';
import HostsEditController from './hosts-edit.controller';

export default
angular.module('manageHosts', [])
    .controller('HostsAddController', HostsAddController)
    .controller('HostEditController', HostsEditController)
    .config(['$stateProvider', 'stateDefinitionsProvider',
        function($stateProvider, stateDefinitionsProvider) {
            let addHost, editHost,
                stateDefinitions = stateDefinitionsProvider.$get();
            addHost = {
                name: 'inventoryManage.addHost',
                url: '/add-host',
                lazyLoad: () => stateDefinitions.generateTree({
                    url: '/add-host',
                    name: 'inventoryManage.addHost',
                    modes: ['add'],
                    form: 'HostForm',
                    controllers: {
                        add: 'HostsAddController'
                    }
                })
            };

            editHost = {
                name: 'inventoryManage.editHost',
                url: '/edit-host/:host_id',
                ncyBreadcrumb: {
                    label: '{{host.name}}',
                },
                lazyLoad: () => stateDefinitions.generateTree({
                    url: '/edit-host/:host_id',
                    name: 'inventoryManage.editHost',
                    modes: ['edit'],
                    form: 'HostForm',
                    controllers: {
                        edit: 'HostEditController'
                    },
                    resolve: {
                        host: ['$stateParams', 'HostManageService', function($stateParams, HostManageService) {
                            return HostManageService.get({ id: $stateParams.host_id }).then(function(res) {
                                return res.data.results[0];
                            });
                        }]
                    }
                })
            };

            $stateProvider.state(addHost);
            $stateProvider.state(editHost);
        }
    ]);
