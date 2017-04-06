/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import host from './hosts/main';
import inventoryAdd from './add/main';
import inventoryEdit from './edit/main';
import inventoryList from './list/main';
import { templateUrl } from '../shared/template-url/template-url.factory';
import { N_ } from '../i18n';
import InventoriesList from './inventory.list';
import InventoriesForm from './inventory.form';
export default
angular.module('inventory', [
        host.name,
        inventoryAdd.name,
        inventoryEdit.name,
        inventoryList.name
    ])
    .factory('InventoriesForm', InventoriesForm)
    .factory('InventoriesList', InventoriesList)
    .config(['$stateProvider', 'stateDefinitionsProvider',
        function($stateProvider, stateDefinitionsProvider) {
            // When stateDefinition.lazyLoad() resolves, states matching name.** or /url** will be de-registered and replaced with resolved states
            // This means inventoryManage states will not be registered correctly on page refresh, unless they're registered at the same time as the inventories state tree
            let stateDefinitions = stateDefinitionsProvider.$get();

                $stateProvider.state({
                    name: 'inventories',
                    url: '/inventories',
                    lazyLoad: () => stateDefinitions.generateTree({
                        parent: 'inventories', // top-most node in the generated tree (will replace this state definition)
                        modes: ['add', 'edit'],
                        list: 'InventoriesList',
                        form: 'InventoriesForm',
                        controllers: {
                            list: 'InventoryListController',
                            add: 'InventoryAddController',
                            edit: 'InventoryEditController'
                        },
                        urls: {
                            list: '/inventories'
                        },
                        ncyBreadcrumb: {
                            label: N_('INVENTORIES')
                        },
                        views: {
                            '@': {
                                templateUrl: templateUrl('inventories/inventories')
                            },
                            'list@inventories': {
                                templateProvider: function(InventoriesList, generateList) {
                                    let html = generateList.build({
                                        list: InventoriesList,
                                        mode: 'edit'
                                    });
                                    return html;
                                },
                                controller: 'InventoryListController'
                            }
                        }
                    })
                });

                $stateProvider.state({
                    name: 'hosts',
                    url: '/hosts',
                    lazyLoad: () => stateDefinitions.generateTree({
                        parent: 'hosts', // top-most node in the generated tree (will replace this state definition)
                        modes: ['add', 'edit'],
                        list: 'HostsList',
                        form: 'HostsForm',
                        controllers: {
                            list: 'HostListController',
                            add: 'HostAddController',
                            edit: 'HostEditController'
                        },
                        urls: {
                            list: '/hosts'
                        },
                        ncyBreadcrumb: {
                            label: N_('HOSTS')
                        },
                        views: {
                            '@': {
                                templateUrl: templateUrl('inventories/inventories')
                            },
                            'list@hosts': {
                                templateProvider: function(HostsList, generateList) {
                                    let html = generateList.build({
                                        list: HostsList,
                                        mode: 'edit'
                                    });
                                    return html;
                                },
                                controller: 'HostListController'
                            }
                        }
                    })
                });
        }
    ]);
