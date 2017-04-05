/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import hostnew from './hosts/main';
import inventoryAdd from './add/main';
import inventoryEdit from './edit/main';
import inventoryList from './list/main';
import { templateUrl } from '../shared/template-url/template-url.factory';
import { N_ } from '../i18n';
// import inventoriesnewRoute from './inventories.route';
import InventoriesNewList from './inventory.list';
import InventoriesNewForm from './inventory.form';
export default
angular.module('inventorynew', [
        hostnew.name,
        inventoryAdd.name,
        inventoryEdit.name,
        inventoryList.name
    ])
    .factory('InventoriesNewForm', InventoriesNewForm)
    .factory('InventoriesNewList', InventoriesNewList)
    .config(['$stateProvider', '$stateExtenderProvider', 'stateDefinitionsProvider',
        function($stateProvider, $stateExtenderProvider, stateDefinitionsProvider) {
            // When stateDefinition.lazyLoad() resolves, states matching name.** or /url** will be de-registered and replaced with resolved states
            // This means inventoryManage states will not be registered correctly on page refresh, unless they're registered at the same time as the inventories state tree
            let stateDefinitions = stateDefinitionsProvider.$get();

                $stateProvider.state({
                    name: 'inventoriesnew',
                    url: '/inventoriesnew',
                    lazyLoad: () => stateDefinitions.generateTree({
                        parent: 'inventoriesnew', // top-most node in the generated tree (will replace this state definition)
                        modes: ['add', 'edit'],
                        list: 'InventoriesNewList',
                        form: 'InventoriesNewForm',
                        controllers: {
                            list: 'NewInventoryListController',
                            add: 'NewInventoryAddController',
                            edit: 'NewInventoryEditController'
                        },
                        ncyBreadcrumb: {
                            label: N_('INVENTORIESNEW')
                        },
                        views: {
                            '@': {
                                templateUrl: templateUrl('inventoriesnew/inventories')
                            },
                            'list@inventoriesnew': {
                                templateProvider: function(InventoriesNewList, generateList) {
                                    let html = generateList.build({
                                        list: InventoriesNewList,
                                        mode: 'edit'
                                    });
                                    return html;
                                },
                                controller: 'NewInventoryListController'
                            }
                        }
                    })
                });

                $stateProvider.state({
                    name: 'hostsnew',
                    url: '/hostsnew',
                    lazyLoad: () => stateDefinitions.generateTree({
                        parent: 'hostsnew', // top-most node in the generated tree (will replace this state definition)
                        modes: ['add', 'edit'],
                        list: 'HostsNewList',
                        form: 'HostsNewForm',
                        controllers: {
                            list: 'NewHostListController',
                            add: 'NewHostAddController',
                            edit: 'NewHostEditController'
                        },
                        ncyBreadcrumb: {
                            label: N_('HOSTSNEW')
                        },
                        views: {
                            '@': {
                                templateUrl: templateUrl('inventoriesnew/inventories')
                            },
                            'list@hostsnew': {
                                templateProvider: function(HostsNewList, generateList) {
                                    let html = generateList.build({
                                        list: HostsNewList,
                                        mode: 'edit'
                                    });
                                    return html;
                                },
                                controller: 'NewHostListController'
                            }
                        }
                    })
                });



            // function generateInvAddStateTree() {
            //
            //     let addInventory = stateDefinitions.generateTree({
            //         url: '/add',
            //         name: 'inventoriesnew.add',
            //         modes: ['add'],
            //         form: 'InventoriesNewForm',
            //         controllers: {
            //             add: 'NewInventoryAddController'
            //         }
            //     });
            //
            //     return Promise.all([
            //         addInventory,
            //     ]).then((generated) => {
            //         return {
            //             states: _.reduce(generated, (result, definition) => {
            //                 return result.concat(definition.states);
            //             }, [])
            //         };
            //     });
            // }
            //
            // function generateInvEditStateTree() {
            //
            //     let editInventory = stateDefinitions.generateTree({
            //         url: '/:inventory_id',
            //         name: 'inventoriesnew.edit',
            //         modes: ['edit'],
            //         form: 'InventoriesNewForm',
            //         controllers: {
            //             edit: 'NewInventoryEditController'
            //         }
            //     });
            //
            //     return Promise.all([
            //         editInventory,
            //     ]).then((generated) => {
            //         return {
            //             states: _.reduce(generated, (result, definition) => {
            //                 return result.concat(definition.states);
            //             }, [])
            //         };
            //     });
            // }
            //
            // let inventoriesnew = {
            //     name: 'inventoriesnew',
            //     route: '/inventoriesnew',
            //     ncyBreadcrumb: {
            //         label: N_("INVENTORIESNEW")
            //     },
            //     params: {
            //         inventory_search: {
            //             value: {order_by: 'name', page_size: '20', role_level: 'admin_role'},
            //             dynamic: true
            //         }
            //     },
            //     resolve: {
            //         Dataset: ['InventoriesNewList', 'QuerySet', '$stateParams', 'GetBasePath', (list, qs, $stateParams, GetBasePath) => {
            //             let path = GetBasePath(list.basePath) || GetBasePath(list.name);
            //             return qs.search(path, $stateParams[`${list.iterator}_search`]);
            //         }],
            //         ListDefinition: ['InventoriesNewList', (list) => {
            //             return list;
            //         }]
            //     },
            //     views: {
            //         '@': {
            //             templateUrl: templateUrl('inventoriesnew/inventories')
            //         },
            //         'list@inventoriesnew': {
            //             templateProvider: function(InventoriesNewList, generateList) {
            //                 let html = generateList.build({
            //                     list: InventoriesNewList,
            //                     mode: 'edit'
            //                 });
            //                 return html;
            //             },
            //             controller: 'NewInventoryListController'
            //         }
            //     }
            // };
            // stateExtender.addState(inventoriesnew);
            //
            // let hostsnew = {
            //     name: 'inventoriesnew.hosts',
            //     route: '/hosts',
            //     ncyBreadcrumb: {
            //         label: N_("HOSTS")
            //     },
            //     params: {
            //         host_search: {
            //             value: {order_by: 'name', page_size: '20'},
            //             dynamic: true
            //         }
            //     },
            //     resolve: {
            //         Dataset: ['HostsNewList', 'QuerySet', '$stateParams', 'GetBasePath', (list, qs, $stateParams, GetBasePath) => {
            //             let path = GetBasePath(list.basePath) || GetBasePath(list.name);
            //             return qs.search(path, $stateParams[`${list.iterator}_search`]);
            //         }],
            //         ListDefinition: ['HostsNewList', (list) => {
            //             return list;
            //         }]
            //     },
            //     views: {
            //         'list@inventoriesnew': {
            //             templateProvider: function(HostsNewList, generateList) {
            //                 let html = generateList.build({
            //                     list: HostsNewList,
            //                     mode: 'edit'
            //                 });
            //                 return html;
            //             },
            //             controller: 'NewHostListController'
            //         }
            //     }
            // };
            // stateExtender.addState(hostsnew);
            //
            // let addInventoryTree = {
            //     name: 'inventoriesnew.add',
            //     url: '/add',
            //     lazyLoad: () => generateInvAddStateTree()
            // };
            // $stateProvider.state(addInventoryTree);
            //
            // let editInventoryTree = {
            //     name: 'inventoriesnew.edit',
            //     url: '/:inventory_id',
            //     lazyLoad: () => generateInvEditStateTree()
            // };
            // $stateProvider.state(editInventoryTree);
        }
    ]);
