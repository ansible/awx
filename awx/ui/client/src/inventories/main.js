/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import adhoc from './adhoc/main';
import host from './hosts/main';
import group from './groups/main';
import sources from './sources/main';
import relatedHost from './related-hosts/main';
import inventoryCompletedJobs from './completed_jobs/main';
import inventoryAdd from './add/main';
import inventoryEdit from './edit/main';
import inventoryList from './list/main';
import { templateUrl } from '../shared/template-url/template-url.factory';
import { N_ } from '../i18n';
import InventoryList from './inventory.list';
import InventoryForm from './inventory.form';
import InventoryManageService from './inventory-manage.service';
import adHocRoute from './adhoc/adhoc.route';
import ansibleFacts from './ansible_facts/main';
import insights from './insights/main';
import { copyMoveGroupRoute, copyMoveHostRoute } from './copy-move/copy-move.route';
import copyMove from './copy-move/main';
export default
angular.module('inventory', [
        adhoc.name,
        host.name,
        group.name,
        sources.name,
        relatedHost.name,
        inventoryCompletedJobs.name,
        inventoryAdd.name,
        inventoryEdit.name,
        inventoryList.name,
        ansibleFacts.name,
        insights.name,
        copyMove.name
    ])
    .factory('InventoryForm', InventoryForm)
    .factory('InventoryList', InventoryList)
    .service('InventoryManageService', InventoryManageService)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider) {
            let stateDefinitions = stateDefinitionsProvider.$get(),
            stateExtender = $stateExtenderProvider.$get();

            function factsConfig(stateName) {
                return {
                    name: stateName,
                    url: '/ansible_facts',
                    ncyBreadcrumb: {
                        label: N_("FACTS")
                    },
                    views: {
                        'related': {
                            controller: 'AnsibleFactsController',
                            templateUrl: templateUrl('inventories/ansible_facts/ansible_facts')
                        }
                    },
                    resolve: {
                        Facts: ['$stateParams', 'GetBasePath', 'Rest',
                            function($stateParams, GetBasePath, Rest) {
                                let ansibleFactsUrl = GetBasePath('hosts') + $stateParams.host_id + '/ansible_facts';
                                Rest.setUrl(ansibleFactsUrl);
                                return Rest.get()
                                    .success(function(data) {
                                        return data;
                                    });
                            }
                        ]
                    }
                };
            }

            function insightsConfig(stateName) {
                return {
                    name: stateName,
                    url: '/insights',
                    ncyBreadcrumb: {
                        label: N_("INSIGHTS")
                    },
                    views: {
                        'related': {
                            controller: 'InsightsController',
                            templateUrl: templateUrl('inventories/insights/insights')
                        }
                    },
                    resolve: {
                        Facts: ['$stateParams', 'GetBasePath', 'Rest',
                            function($stateParams, GetBasePath, Rest) {
                                let ansibleFactsUrl = GetBasePath('hosts') + $stateParams.host_id + '/ansible_facts';
                                Rest.setUrl(ansibleFactsUrl);
                                return Rest.get()
                                    .success(function(data) {
                                        return data;
                                    });
                            }
                        ]
                    }
                };
            }

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

                let adhocCredentialLookup = {
                    searchPrefix: 'credential',
                    name: 'inventories.edit.adhoc.credential',
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
                    }
                };

                let listSchedules = {
                    name: 'inventories.edit.inventory_sources.edit.schedules',
                    url: '/schedules',
                    searchPrefix: 'schedule',
                    ncyBreadcrumb: {
                        label: N_('SCHEDULES')
                    },
                    resolve: {
                        Dataset: ['ScheduleList', 'QuerySet', '$stateParams', 'GetBasePath', 'inventorySourceData',
                            function(list, qs, $stateParams, GetBasePath, inventorySourceData) {
                                let path = `${inventorySourceData.related.schedules}`;
                                return qs.search(path, $stateParams[`${list.iterator}_search`]);
                            }
                        ],
                        ParentObject: ['inventorySourceData', function(inventorySourceData) {
                            return inventorySourceData;
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
                        ScheduleList: ['SchedulesList', 'inventorySourceData',
                            (SchedulesList, inventorySourceData) => {
                                let list = _.cloneDeep(SchedulesList);
                                list.basePath = `${inventorySourceData.related.schedules}`;
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

                let addSchedule = {
                    name: 'inventories.edit.inventory_sources.edit.schedules.add',
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

                let editSchedule = {
                    name: 'inventories.edit.inventory_sources.edit.schedules.edit',
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

                let relatedHostsAnsibleFacts = factsConfig('inventories.edit.hosts.edit.ansible_facts');
                let nestedHostsAnsibleFacts =  factsConfig('inventories.edit.groups.edit.nested_hosts.edit.ansible_facts');
                let relatedHostsInsights = insightsConfig('inventories.edit.hosts.edit.insights');
                let nestedHostsInsights =  insightsConfig('inventories.edit.groups.edit.nested_hosts.edit.insights');

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
                            }),
                            stateExtender.buildDefinition(adHocRoute),
                            stateExtender.buildDefinition(adhocCredentialLookup),
                            stateExtender.buildDefinition(listSchedules),
                            stateExtender.buildDefinition(addSchedule),
                            stateExtender.buildDefinition(editSchedule),
                            stateExtender.buildDefinition(relatedHostsAnsibleFacts),
                            stateExtender.buildDefinition(nestedHostsAnsibleFacts),
                            stateExtender.buildDefinition(relatedHostsInsights),
                            stateExtender.buildDefinition(nestedHostsInsights),
                            stateExtender.buildDefinition(copyMoveGroupRoute),
                            stateExtender.buildDefinition(copyMoveHostRoute)
                        ])
                    };
                });

            }

            let generateHostStates = function(){
                let hostTree = stateDefinitions.generateTree({
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
                });

                let hostAnsibleFacts = factsConfig('hosts.edit.ansible_facts');
                let hostInsights = insightsConfig('hosts.edit.insights');

                return Promise.all([
                    hostTree
                ]).then((generated) => {
                    return {
                        states: _.reduce(generated, (result, definition) => {
                            return result.concat(definition.states);
                        }, [
                            stateExtender.buildDefinition(hostAnsibleFacts),
                            stateExtender.buildDefinition(hostInsights)
                        ])
                    };
                });
            };

            $stateProvider.state({
                name: 'hosts',
                url: '/hosts',
                lazyLoad: () => generateHostStates()
            });

            $stateProvider.state({
                name: 'inventories',
                url: '/inventories',
                lazyLoad: () => generateInventoryStates()
            });
        }
    ]);
