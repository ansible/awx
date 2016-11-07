/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobTemplateService from './job-template.service';

import surveyMaker from './survey-maker/main';
import jobTemplatesList from './list/main';
import jobTemplatesAdd from './add-job-template/main';
import jobTemplatesEdit from './edit-job-template/main';
import jobTemplatesCopy from './copy/main';
import workflowAdd from './add-workflow/main';
import workflowEdit from './edit-workflow/main';
import labels from './labels/main';
import workflowChart from './workflow-chart/main';
import workflowMaker from './workflow-maker/main';
import jobTemplatesListRoute from './list/job-templates-list.route';

export default
angular.module('jobTemplates', [surveyMaker.name, jobTemplatesList.name, jobTemplatesAdd.name,
        jobTemplatesEdit.name, jobTemplatesCopy.name, labels.name, workflowAdd.name, workflowEdit.name,
        workflowChart.name, workflowMaker.name
    ])
    .service('JobTemplateService', jobTemplateService)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider) {
            let stateTree, addJobTemplate, editJobTemplate, addWorkflow, editWorkflow,
                workflowMaker, inventoryLookup, credentialLookup,
                stateDefinitions = stateDefinitionsProvider.$get(),
                stateExtender = $stateExtenderProvider.$get();

            function generateStateTree() {

                addJobTemplate = stateDefinitions.generateTree({
                    name: 'templates.addJobTemplate',
                    url: '/add_job_template',
                    modes: ['add'],
                    form: 'JobTemplateForm',
                    controllers: {
                        add: 'JobTemplateAdd'
                    }
                });

                editJobTemplate = stateDefinitions.generateTree({
                    name: 'templates.editJobTemplate',
                    url: '/job_template/:job_template_id',
                    modes: ['edit'],
                    form: 'JobTemplateForm',
                    controllers: {
                        edit: 'JobTemplateEdit'
                    }
                });

                addWorkflow = stateDefinitions.generateTree({
                    name: 'templates.addWorkflowJobTemplate',
                    url: '/add_workflow_job_template',
                    modes: ['add'],
                    form: 'WorkflowForm',
                    controllers: {
                        add: 'WorkflowAdd'
                    }
                });

                editWorkflow = stateDefinitions.generateTree({
                    name: 'templates.editWorkflowJobTemplate',
                    url: '/workflow_job_template/:workflow_job_template_id',
                    modes: ['edit'],
                    form: 'WorkflowForm',
                    controllers: {
                        edit: 'WorkflowEdit'
                    }
                });

                workflowMaker = {
                    name: 'templates.editWorkflowJobTemplate.workflowMaker',
                    url: '/workflow-maker',
                    // ncyBreadcrumb: {
                    //     label: 'WORKFLOW MAKER'
                    // },
                    data: {
                        formChildState: true
                    },
                    params: {
                        job_template_search: {
                            value: {
                                page_size: '5',
                                type: 'job_template'
                            },
                            squash: true,
                            dynamic: true
                        },
                        project_search: {
                            value: {
                                page_size: '5'
                            },
                            squash: true,
                            dynamic: true
                        },
                        inventory_source_search: {
                            value: {
                                page_size: '5'
                            },
                            squash: true,
                            dynamic: true
                        }
                    },
                    views: {
                        'modal': {
                            template: ` <workflow-maker ng-if="includeWorkflowMaker" tree-data="workflowTree"></workflow-maker>`
                        },
                        'jobTemplateList@templates.editWorkflowJobTemplate.workflowMaker': {
                            templateProvider: function(WorkflowMakerJobTemplateList, generateList) {
                                //debugger;
                                let html = generateList.build({
                                    list: WorkflowMakerJobTemplateList,
                                    input_type: 'radio',
                                    mode: 'lookup'
                                });
                                return html;
                            },
                            // $scope encapsulated in this controller will be a initialized as child of 'modal' $scope, because of element hierarchy
                            controller: ['$scope', 'WorkflowMakerJobTemplateList', 'JobTemplateDataset',
                                function($scope, list, Dataset) {

                                    init();

                                    function init() {
                                        $scope.list = list;
                                        $scope[`${list.iterator}_dataset`] = Dataset.data;
                                        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
                                    }

                                    $scope.toggle_job_template = function(id) {

                                        $scope.job_templates.forEach(function(row, i) {
                                            if (row.id === id) {
                                                $scope.job_templates[i].checked = 1;
                                                $scope.selection[list.iterator] = {
                                                    id: row.id,
                                                    name: row.name
                                                };

                                                $scope.$emit('templateSelected', row);
                                            }
                                        });

                                    };

                                    $scope.$on('clearOtherTemplateLists', function(e, tab) {
                                        if(tab !== 'jobs') {
                                            // Clear out any selected job
                                        }
                                    });
                                }
                            ]
                        },
                        'inventorySyncList@templates.editWorkflowJobTemplate.workflowMaker': {
                            templateProvider: function(InventorySourcesList, generateList) {
                                let list = _.cloneDeep(InventorySourcesList);
                                // mutate list definition here!
                                let html = generateList.build({
                                    list: list,
                                    input_type: 'radio',
                                    mode: 'lookup'
                                });
                                return html;
                            },
                            // encapsulated $scope in this controller will be a initialized as child of 'modal' $scope, because of element hierarchy
                            controller: ['$scope', 'InventorySourcesList', 'InventorySourcesDataset',
                                function($scope, list, Dataset) {

                                    init();

                                    function init() {
                                        $scope.list = list;
                                        $scope[`${list.iterator}_dataset`] = Dataset.data;
                                        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

                                    }

                                    $scope.toggle_inventory_source = function(id) {

                                        $scope.inventory_sources.forEach(function(row, i) {
                                            if (row.id === id) {
                                                $scope.inventory_sources[i].checked = 1;
                                                $scope.selection[list.iterator] = {
                                                    id: row.id,
                                                    name: row.name
                                                };

                                                $scope.$emit('templateSelected', row);
                                            }
                                        });

                                    };

                                    $scope.$on('clearOtherTemplateLists', function(e, tab) {
                                        if(tab !== 'project_sync') {

                                        }
                                    });
                                }
                            ]
                        },
                        'projectSyncList@templates.editWorkflowJobTemplate.workflowMaker': {
                            templateProvider: function(WorkflowProjectList, generateList) {
                                let html = generateList.build({
                                    list: WorkflowProjectList,
                                    input_type: 'radio',
                                    mode: 'lookup'
                                });
                                return html;
                            },
                            // encapsulated $scope in this controller will be a initialized as child of 'modal' $scope, because of element hierarchy
                            controller: ['$scope', 'WorkflowProjectList', 'ProjectDataset',
                                function($scope, list, Dataset) {

                                    init();

                                    function init() {
                                        $scope.list = list;
                                        $scope[`${list.iterator}_dataset`] = Dataset.data;
                                        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

                                    }

                                    $scope.toggle_project = function(id) {

                                        $scope.projects.forEach(function(row, i) {
                                            if (row.id === id) {
                                                $scope.projects[i].checked = 1;
                                                $scope.selection[list.iterator] = {
                                                    id: row.id,
                                                    name: row.name
                                                };

                                                $scope.$emit('templateSelected', row);
                                            }
                                        });

                                    };

                                    $scope.$on('clearOtherTemplateLists', function(e, tab) {
                                        if(tab !== 'inventory_sync') {

                                        }
                                    });
                                }
                            ]
                        },
                        'workflowForm@templates.editWorkflowJobTemplate.workflowMaker': {
                            templateProvider: function(WorkflowMakerForm, GenerateForm) {
                                let form = WorkflowMakerForm();
                                let html = GenerateForm.buildHTML(form, {
                                    mode: 'add',
                                    related: false,
                                    noPanel: true
                                });
                                return html;
                            }
                        }
                    },
                    resolve: {
                        JobTemplateDataset: ['WorkflowMakerJobTemplateList', 'QuerySet', '$stateParams', 'GetBasePath',
                            (list, qs, $stateParams, GetBasePath) => {
                                let path = GetBasePath(list.basePath);
                                return qs.search(path, $stateParams[`${list.iterator}_search`]);
                            }
                        ],
                        ProjectDataset: ['ProjectList', 'QuerySet', '$stateParams', 'GetBasePath',
                            (list, qs, $stateParams, GetBasePath) => {
                                let path = GetBasePath(list.basePath);
                                return qs.search(path, $stateParams[`${list.iterator}_search`]);
                            }
                        ],
                        InventorySourcesDataset: ['InventorySourcesList', 'QuerySet', '$stateParams', 'GetBasePath',
                            (list, qs, $stateParams, GetBasePath) => {
                                let path = GetBasePath(list.basePath);
                                return qs.search(path, $stateParams[`${list.iterator}_search`]);
                            }
                        ],
                        WorkflowMakerJobTemplateList: ['JobTemplateList',
                            (JobTemplateList) => {
                                let list = _.cloneDeep(JobTemplateList);
                                delete list.fields.type;
                                delete list.fields.description;
                                delete list.fields.smart_status;
                                delete list.fields.labels;
                                delete list.fieldActions;
                                list.fields.name.columnClass = "col-md-11";
                                list.iterator = 'job_template';
                                list.name = 'job_templates';

                                return list;
                            }
                        ],
                        WorkflowProjectList: ['ProjectList',
                            (ProjectList) => {
                                let list = _.cloneDeep(ProjectList);
                                delete list.fields.status;
                                delete list.fields.scm_type;
                                delete list.fields.last_updated;
                                list.fields.name.columnClass = "col-md-11";

                                return list;
                            }
                        ]
                    }
                };

                inventoryLookup = {
                    searchPrefix: 'inventory',
                    name: 'templates.editWorkflowJobTemplate.workflowMaker.inventory',
                    url: '/inventory',
                    data: {
                        formChildState: true
                    },
                    params: {
                        inventory_search: {
                            value: {
                                page_size: '5'
                            },
                            squash: true,
                            dynamic: true
                        }
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
                        ListDefinition: ['InventoryList', function(list) {
                            // mutate the provided list definition here
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

                credentialLookup = {
                    searchPrefix: 'credential',
                    name: 'templates.editWorkflowJobTemplate.workflowMaker.credential',
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
                        ListDefinition: ['CredentialList', function(list) {
                            // mutate the provided list definition here
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
                    addJobTemplate,
                    editJobTemplate,
                    addWorkflow,
                    editWorkflow
                ]).then((generated) => {
                    return {
                        states: _.reduce(generated, (result, definition) => {
                            return result.concat(definition.states);
                        }, [
                            stateExtender.buildDefinition(jobTemplatesListRoute),
                            stateExtender.buildDefinition(workflowMaker),
                            stateExtender.buildDefinition(inventoryLookup),
                            stateExtender.buildDefinition(credentialLookup)
                        ])
                    };
                });
            }

            stateTree = {
                name: 'templates',
                url: '/templates',
                lazyLoad: () => generateStateTree()
            };

            $stateProvider.state(stateTree);

        }
    ]);
