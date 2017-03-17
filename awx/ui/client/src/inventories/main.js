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
import { N_ } from '../i18n';

// actual inventory list config object
import InventoryList from './inventory.list';

export default
angular.module('inventory', [
        inventoryAdd.name,
        inventoryEdit.name,
        inventoryList.name,
        inventoryManage.name,
    ])
    .factory('InventoryList', InventoryList)
    .config(['$stateProvider', '$stateExtenderProvider', 'stateDefinitionsProvider',
        function($stateProvider, $stateExtenderProvider, stateDefinitionsProvider) {
            // When stateDefinition.lazyLoad() resolves, states matching name.** or /url** will be de-registered and replaced with resolved states
            // This means inventoryManage states will not be registered correctly on page refresh, unless they're registered at the same time as the inventories state tree
            let stateTree, inventories,
                addGroup, editGroup, addHost, editHost,
                listSchedules, addSchedule, editSchedule, adhocCredentialLookup,
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
                    },
                    ncyBreadcrumb: {
                        label: N_('INVENTORIES')
                    }
                });

                // scheduler state nodes
                listSchedules = {
                    name: 'inventoryManage.editGroup.schedules',
                    url: '/schedules',
                    searchPrefix: 'schedule',
                    ncyBreadcrumb: {
                        parent: 'inventoryManage({group_id: parentObject.id})',
                        label: N_('SCHEDULES')
                    },
                    resolve: {
                        Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath', 'groupData',
                            function(list, qs, $stateParams, GetBasePath, groupData) {
                                let path = `${groupData.related.inventory_source}schedules`;
                                return qs.search(path, $stateParams[`${list.iterator}_search`]);
                            }
                        ],
                        ParentObject: ['groupData', function(groupData) {
                            return groupData;
                        }],
                        UnifiedJobsOptions: ['Rest', 'GetBasePath', '$stateParams', '$q',
                            function(Rest, GetBasePath, $stateParams, $q) {
                                Rest.setUrl(GetBasePath('unified_jobs'));
                                var val = $q.defer();
                                Rest.options()
                                    .then(function(data) {
                                        val.resolve(data.data);
                                    }, function(data) {
                                        val.reject(data);
                                    });
                                return val.promise;
                            }],
                        ScheduleList: ['SchedulesList', 'groupData',
                            (SchedulesList, groupData) => {
                                let list = _.cloneDeep(SchedulesList);
                                list.basePath = `${groupData.related.inventory_source}schedules`;
                                return list;
                            }
                        ]
                    },
                    views: {
                        // clear form template when views render in this substate
                        'form': {
                            templateProvider: () => ''
                        },
                        // target the un-named ui-view @ root level
                        '@': {
                            templateProvider: function(ScheduleList, generateList, ParentObject) {
                                // include name of parent resource in listTitle
                                ScheduleList.listTitle = `${ParentObject.name}<div class='List-titleLockup'></div>` + N_('SCHEDULES');
                                let html = generateList.build({
                                    list: ScheduleList,
                                    mode: 'edit'
                                });
                                html = generateList.wrapPanel(html);
                                return "<div class='InventoryManage-container'>" + generateList.insertFormView() + html + "</div>";
                            },
                            controller: 'schedulerListController'
                        }
                    }
                };

                addSchedule = {
                    name: 'inventoryManage.editGroup.schedules.add',
                    url: '/add',
                    ncyBreadcrumb: {
                        label: N_("CREATE SCHEDULE")
                    },
                    views: {
                        'form': {
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
                        'form': {
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

                adhocCredentialLookup = {
                    searchPrefix: 'credential',
                    name: 'inventoryManage.adhoc.credential',
                    url: '/credential',
                    data: {
                        formChildState: true
                    },
                    params: {
                        credential_search: {
                            value: {
                                page_size: '5'
                            },
                            squash: true,
                            dynamic: true
                        }
                    },
                    ncyBreadcrumb: {
                        skip: true
                    },
                    views: {
                        'related': {
                            templateProvider: function(ListDefinition, generateList) {
                                let list_html = generateList.build({
                                    mode: 'lookup',
                                    list: ListDefinition,
                                    input_type: 'radio'
                                });
                                return `<lookup-modal>${list_html}</lookup-modal>`;

                            }
                        }
                    },
                    resolve: {
                        ListDefinition: ['CredentialList', function(CredentialList) {
                            let list = _.cloneDeep(CredentialList);
                            list.lookupConfirmText = 'SELECT';
                            return list;
                        }],
                        Dataset: ['ListDefinition', 'QuerySet', '$stateParams', 'GetBasePath',
                            (list, qs, $stateParams, GetBasePath) => {
                                let path = GetBasePath(list.name) || GetBasePath(list.basePath);
                                return qs.search(path, $stateParams[`${list.iterator}_search`]);
                            }
                        ]
                    },
                    onExit: function($state) {
                        if ($state.transition) {
                            $('#form-modal').modal('hide');
                            $('.modal-backdrop').remove();
                            $('body').removeClass('modal-open');
                        }
                    },
                };

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
                            stateExtender.buildDefinition(adhocCredentialLookup)

                        ])
                    };
                });
            }

            stateTree = {
                name: 'inventories',
                url: '/inventories',
                ncyBreadcrumb: {
                    label: N_("INVENTORIES")
                },
                lazyLoad: () => generateStateTree()
            };

            $stateProvider.state(stateTree);
        }
    ]);
