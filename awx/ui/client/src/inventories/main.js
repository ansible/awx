/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import inventoryAdd from './add/main';
import inventoryEdit from './edit/main';
import inventoryList from './list/main';
import inventoryManage from './manage/main';
import inventoryManageListRoute from './manage/inventory-manage.route';
import { copyMoveGroupRoute, copyMoveHostRoute } from './manage/copy-move/copy-move.route';
import adHocRoute from './manage/adhoc/adhoc.route';
import { templateUrl } from '../shared/template-url/template-url.factory';
export default
angular.module('inventory', [
        inventoryAdd.name,
        inventoryEdit.name,
        inventoryList.name,
        inventoryManage.name,
    ])
    .config(['$stateProvider', '$stateExtenderProvider', 'stateDefinitionsProvider',
        function($stateProvider, $stateExtenderProvider, stateDefinitionsProvider) {
            // When stateDefinition.lazyLoad() resolves, states matching name.** or /url** will be de-registered and replaced with resolved states
            // This means inventoryManage states will not be registered correctly on page refresh, unless they're registered at the same time as the inventories state tree
            let stateTree, inventories,
                addGroup, editGroup, addHost, editHost,
                listSchedules, addSchedule, editSchedule,
                stateDefinitions = stateDefinitionsProvider.$get(),
                stateExtender = $stateExtenderProvider.$get();

            function generateStateTree() {

                // inventories state node
                inventories = stateDefinitions.generateTree({
                    parent: 'inventories', // top-most node in the generated tree (will replace this state definition)
                    modes: ['add', 'edit'],
                    list: 'InventoryList',
                    form: 'InventoryForm',
                    controllers: {
                        list: 'InventoryListController',
                        add: 'InventoryAddController',
                        edit: 'InventoryEditController'
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'inventory'
                    }
                });

                // scheduler state nodes
                listSchedules = {
                    name: 'inventoryManage.editGroup.schedules',
                    url: '/schedules',
                    searchPrefix: 'schedule',
                    ncyBreadcrumb: {
                        parent: 'inventoryManage.editGroup({group_id: parentObject.id})',
                        label: 'SCHEDULES'
                    },
                    resolve: {
                        Dataset: ['SchedulesList', 'QuerySet', '$stateParams', 'GetBasePath', 'groupData',
                            function(list, qs, $stateParams, GetBasePath, groupData) {
                                let path = `${groupData.related.inventory_source}schedules`;
                                return qs.search(path, $stateParams[`${list.iterator}_search`]);
                            }
                        ],
                        ParentObject: ['groupData', function(groupData) {
                            return groupData;
                        }]
                    },
                    views: {
                        // clear form template when views render in this substate
                        'form@': {
                            templateProvider: () => ''
                        },
                        'list@': {
                            templateProvider: function(SchedulesList, generateList, ParentObject) {
                                // include name of parent resource in listTitle
                                SchedulesList.listTitle = `${ParentObject.name}<div class='List-titleLockup'></div>Schedules`;
                                let html = generateList.build({
                                    list: SchedulesList,
                                    mode: 'edit'
                                });
                                html = generateList.wrapPanel(html);
                                return html;
                            },
                            controller: 'schedulerListController'
                        }
                    }
                };

                addSchedule = {
                    name: 'inventoryManage.editGroup.schedules.add',
                    url: '/add',
                    ncyBreadcrumb: {
                        label: "CREATE SCHEDULE"
                    },
                    views: {
                        'form@': {
                            controller: 'schedulerAddController',
                            templateUrl: templateUrl("scheduler/schedulerForm")
                        }
                    }
                };

                editSchedule = {
                    name: 'inventoryManage.editGroup.schedules.edit',
                    url: '/:schedule_id',
                    ncyBreadcrumb: {
                        label: "{{schedule_obj.name}}"
                    },
                    views: {
                        'form@': {
                            templateUrl: templateUrl("scheduler/schedulerForm"),
                            controller: 'schedulerEditController',
                        }
                    }
                };

                // group state nodes
                addGroup = stateDefinitions.generateTree({
                    url: '/add-group',
                    name: 'inventoryManage.addGroup',
                    modes: ['add'],
                    form: 'GroupForm',
                    controllers: {
                        add: 'GroupAddController'
                    }
                });

                editGroup = stateDefinitions.generateTree({
                    //parent: 'inventoryManage', // top-most node in the generated tree (tree will replace this node)
                    url: '/edit-group/:group_id',
                    name: 'inventoryManage.editGroup',
                    modes: ['edit'],
                    form: 'GroupForm',
                    controllers: {
                        edit: 'GroupEditController'
                    },
                    resolve: {
                        edit: {
                            groupData: ['$stateParams', 'GroupManageService', function($stateParams, GroupManageService) {
                                return GroupManageService.get({ id: $stateParams.group_id }).then(res => res.data.results[0]);
                            }],
                            inventorySourceData: ['$stateParams', 'GroupManageService', function($stateParams, GroupManageService) {
                                return GroupManageService.getInventorySource({ group: $stateParams.group_id }).then(res => res.data.results[0]);
                            }]
                        }
                    },
                    // concat boilerplate schedule state definitions with generated editGroup state definitions
                }).then((generated) => {
                    let schedulerDefinitions = _.map([
                            stateExtender.buildDefinition(listSchedules),
                            stateExtender.buildDefinition(addSchedule),
                            stateExtender.buildDefinition(editSchedule)
                        ],
                        (state) => stateExtender.buildDefinition(state));
                    return {
                        states: _(generated.states)
                            .concat(schedulerDefinitions)
                            .value()
                    };
                });

                // host state nodes
                addHost = stateDefinitions.generateTree({
                    url: '/add-host',
                    name: 'inventoryManage.addHost',
                    modes: ['add'],
                    form: 'HostForm',
                    controllers: {
                        add: 'HostsAddController'
                    }
                });

                editHost = stateDefinitions.generateTree({
                    url: '/edit-host/:host_id',
                    name: 'inventoryManage.editHost',
                    modes: ['edit'],
                    form: 'HostForm',
                    controllers: {
                        edit: 'HostEditController'
                    },
                    resolve: {
                        edit: {
                            host: ['$stateParams', 'HostManageService', function($stateParams, HostManageService) {
                                return HostManageService.get({ id: $stateParams.host_id }).then(function(res) {
                                    return res.data.results[0];
                                });
                            }]
                        }
                    },
                    ncyBreadcrumb: {
                        label: "{{host.name}}",
                    },
                });

                return Promise.all([
                    inventories,
                    addGroup,
                    editGroup,
                    addHost,
                    editHost,
                ]).then((generated) => {
                    return {
                        states: _.reduce(generated, (result, definition) => {
                            return result.concat(definition.states);
                        }, [
                            stateExtender.buildDefinition(inventoryManageListRoute),
                            stateExtender.buildDefinition(copyMoveGroupRoute),
                            stateExtender.buildDefinition(copyMoveHostRoute),
                            stateExtender.buildDefinition(adHocRoute),

                        ])
                    };
                });
            }

            stateTree = {
                name: 'inventories',
                url: '/inventories',
                lazyLoad: () => generateStateTree()
            };

            $stateProvider.state(stateTree);
        }
    ]);
