/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import host from './hosts/main';
import group from './groups/main';
import relatedHost from './related-hosts/main';
import inventoryAdd from './add/main';
import inventoryEdit from './edit/main';
import inventoryList from './list/main';
import { templateUrl } from '../shared/template-url/template-url.factory';
import { N_ } from '../i18n';
import InventoryList from './inventory.list';
import InventoryForm from './inventory.form';
import InventoryManageService from './inventory-manage.service';
export default
angular.module('inventory', [
        host.name,
        group.name,
        relatedHost.name,
        inventoryAdd.name,
        inventoryEdit.name,
        inventoryList.name
    ])
    .factory('InventoryForm', InventoryForm)
    .factory('InventoryList', InventoryList)
    .service('InventoryManageService', InventoryManageService)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider) {
            // When stateDefinition.lazyLoad() resolves, states matching name.** or /url** will be de-registered and replaced with resolved states
            // This means inventoryManage states will not be registered correctly on page refresh, unless they're registered at the same time as the inventories state tree
            let stateDefinitions = stateDefinitionsProvider.$get(),
            stateExtender = $stateExtenderProvider.$get();


            function generateInventoryStates() {

                let basicInventoryAdd = stateDefinitions.generateTree({
                    name: 'inventories.add', // top-most node in the generated tree (will replace this state definition)
                    url: '/basic_inventory/add',
                    modes: ['add'],
                    form: 'InventoryForm',
                    controllers: {
                        add: 'InventoryAddController'
                    }
                });

                let basicInventoryEdit = stateDefinitions.generateTree({
                    name: 'inventories.edit',
                    url: '/basic_inventory/:inventory_id',
                    modes: ['edit'],
                    form: 'InventoryForm',
                    controllers: {
                        edit: 'InventoryEditController'
                    }
                });

                let smartInventoryAdd = stateDefinitions.generateTree({
                    name: 'inventories.addSmartInventory', // top-most node in the generated tree (will replace this state definition)
                    url: '/smart_inventory/add?hostfilter',
                    modes: ['add'],
                    form: 'SmartInventoryForm',
                    controllers: {
                        add: 'SmartInventoryAddController'
                    }
                });

                let smartInventoryEdit = stateDefinitions.generateTree({
                    name: 'inventories.editSmartInventory',
                    url: '/smart_inventory/:inventory_id',
                    modes: ['edit'],
                    form: 'SmartInventoryForm',
                    controllers: {
                        edit: 'SmartInventoryEditController'
                    }
                });

                return Promise.all([
                    basicInventoryAdd,
                    basicInventoryEdit,
                    smartInventoryAdd,
                    smartInventoryEdit
                ]).then((generated) => {
                    return {
                        states: _.reduce(generated, (result, definition) => {
                            return result.concat(definition.states);
                        }, [
                            stateExtender.buildDefinition({
                                name: 'inventories', // top-most node in the generated tree (will replace this state definition)
                                route: '/inventories',
                                ncyBreadcrumb: {
                                    label: N_('INVENTORIES')
                                },
                                views: {
                                    '@': {
                                        templateUrl: templateUrl('inventories/inventories')
                                    },
                                    'list@inventories': {
                                        templateProvider: function(InventoryList, generateList) {
                                            let html = generateList.build({
                                                list: InventoryList,
                                                mode: 'edit'
                                            });
                                            return html;
                                        },
                                        controller: 'InventoryListController'
                                    }
                                },
                                searchPrefix: 'inventory',
                                resolve: {
                                    Dataset: ['InventoryList', 'QuerySet', '$stateParams', 'GetBasePath',
                                        function(list, qs, $stateParams, GetBasePath) {
                                            let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                                            return qs.search(path, $stateParams[`${list.iterator}_search`]);
                                        }
                                    ]
                                }
                            })
                        ])
                    };
                });

            }

                $stateProvider.state({
                    name: 'hosts',
                    url: '/hosts',
                    lazyLoad: () => stateDefinitions.generateTree({
                        parent: 'hosts', // top-most node in the generated tree (will replace this state definition)
                        modes: ['edit'],
                        list: 'HostsList',
                        form: 'HostsForm',
                        controllers: {
                            list: 'HostListController',
                            edit: 'HostEditController'
                        },
                        urls: {
                            list: '/hosts'
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

                $stateProvider.state({
                    name: 'inventories',
                    url: '/inventories',
                    lazyLoad: () => generateInventoryStates()
                });
        }
    ]);
