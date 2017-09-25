/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import templatesService from './templates.service';
import surveyMaker from './survey-maker/main';
import templatesList from './list/main';
import jobTemplates from './job_templates/main';
import workflowAdd from './workflows/add-workflow/main';
import workflowEdit from './workflows/edit-workflow/main';
import labels from './labels/main';
import workflowChart from './workflows/workflow-chart/main';
import workflowMaker from './workflows/workflow-maker/main';
import workflowControls from './workflows/workflow-controls/main';
import templatesListRoute from './list/templates-list.route';
import workflowService from './workflows/workflow.service';
import templateCopyService from './copy-template/template-copy.service';
import WorkflowForm from './workflows.form';
import CompletedJobsList from './completed-jobs.list';
import InventorySourcesList from './inventory-sources.list';
import TemplateList from './templates.list';

export default
angular.module('templates', [surveyMaker.name, templatesList.name, jobTemplates.name, labels.name, workflowAdd.name, workflowEdit.name,
        workflowChart.name, workflowMaker.name, workflowControls.name
    ])
    .service('TemplatesService', templatesService)
    .service('WorkflowService', workflowService)
    .service('TemplateCopyService', templateCopyService)
    .factory('WorkflowForm', WorkflowForm)
    .factory('CompletedJobsList', CompletedJobsList)
    .factory('TemplateList', TemplateList)
    .value('InventorySourcesList', InventorySourcesList)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider) {
            let stateTree, addJobTemplate, editJobTemplate, addWorkflow, editWorkflow,
                workflowMaker, inventoryLookup, credentialLookup,
                stateDefinitions = stateDefinitionsProvider.$get(),
                stateExtender = $stateExtenderProvider.$get();

            function generateStateTree() {

                addJobTemplate = stateDefinitions.generateTree({
                    name: 'templates.addJobTemplate',
                    url: '/add_job_template?inventory_id&credential_id',
                    modes: ['add'],
                    form: 'JobTemplateForm',
                    controllers: {
                        add: 'JobTemplateAdd'
                    },
                    resolve: {
                        add: {
                            Inventory: ['$stateParams', 'Rest', 'GetBasePath', 'ProcessErrors',
                                function($stateParams, Rest, GetBasePath, ProcessErrors){
                                    if($stateParams.inventory_id){
                                        let path = `${GetBasePath('inventory')}${$stateParams.inventory_id}`;
                                        Rest.setUrl(path);
                                        return Rest.get().
                                            then(function(data){
                                                return data.data;
                                            }).catch(function(response) {
                                                ProcessErrors(null, response.data, response.status, null, {
                                                    hdr: 'Error!',
                                                    msg: 'Failed to get inventory info. GET returned status: ' +
                                                        response.status
                                                });
                                            });
                                    }
                            }],
                            Project: ['$stateParams', 'Rest', 'GetBasePath', 'ProcessErrors',
                                function($stateParams, Rest, GetBasePath, ProcessErrors){
                                    if($stateParams.credential_id){
                                        let path = `${GetBasePath('projects')}?credential__id=${Number($stateParams.credential_id)}`;
                                        Rest.setUrl(path);
                                        return Rest.get().
                                            then(function(data){
                                                return data.data.results[0];
                                            }).catch(function(response) {
                                                ProcessErrors(null, response.data, response.status, null, {
                                                    hdr: 'Error!',
                                                    msg: 'Failed to get project info. GET returned status: ' +
                                                        response.status
                                                });
                                            });
                                    }
                            }],
                            availableLabels: ['ProcessErrors', 'TemplatesService',
                                function(ProcessErrors, TemplatesService) {
                                    return TemplatesService.getAllLabelOptions()
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get labels. GET returned status: ' +
                                                    response.status
                                            });
                                        });
                            }],
                            checkPermissions: ['Rest', 'GetBasePath', 'TemplatesService', 'Alert', 'ProcessErrors', '$state',
                                function(Rest, GetBasePath, TemplatesService, Alert, ProcessErrors, $state) {
                                    return TemplatesService.getJobTemplateOptions()
                                        .then(function(data) {
                                            if (!data.actions.POST) {
                                                $state.go("^");
                                                Alert('Permission Error', 'You do not have permission to add a job template.', 'alert-info');
                                            }
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get job template options. OPTIONS returned status: ' +
                                                    response.status
                                            });
                                        });
                                    }]
                        }
                    }
                });

                editJobTemplate = stateDefinitions.generateTree({
                    name: 'templates.editJobTemplate',
                    url: '/job_template/:job_template_id',
                    modes: ['edit'],
                    form: 'JobTemplateForm',
                    controllers: {
                        edit: 'JobTemplateEdit',
                        related: {
                            completed_jobs: 'JobsList'
                        }
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'job_template',
                        activityStreamId: 'job_template_id'
                    },
                    resolve: {
                        edit: {
                            jobTemplateData: ['$stateParams', 'TemplatesService', 'ProcessErrors',
                                function($stateParams, TemplatesService, ProcessErrors) {
                                    return TemplatesService.getJobTemplate($stateParams.job_template_id)
                                        .then(function(res) {
                                            return res.data;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get job template. GET returned status: ' +
                                                    response.status
                                            });
                                        });
                            }],
                            projectGetPermissionDenied: ['Rest', 'ProcessErrors', 'jobTemplateData',
                                function(Rest, ProcessErrors, jobTemplateData) {
                                    if(jobTemplateData.related.project) {
                                        Rest.setUrl(jobTemplateData.related.project);
                                        return Rest.get()
                                            .then(() => {
                                                return false;
                                            })
                                            .catch(({data, status}) => {
                                                if (status !== 403) {
                                                    ProcessErrors(null, data, status, null, {
                                                        hdr: 'Error!',
                                                        msg: 'Failed to get project. GET returned ' +
                                                            'status: ' + status
                                                    });
                                                    return false;
                                                }
                                                else {
                                                    return true;
                                                }
                                        });
                                    }
                                    else {
                                        return false;
                                    }
                            }],
                            inventoryGetPermissionDenied: ['Rest', 'ProcessErrors', 'jobTemplateData',
                                function(Rest, ProcessErrors, jobTemplateData) {
                                    if(jobTemplateData.related.inventory) {
                                        Rest.setUrl(jobTemplateData.related.inventory);
                                        return Rest.get()
                                            .then(() => {
                                                return false;
                                            })
                                            .catch(({data, status}) => {
                                                if (status !== 403) {
                                                    ProcessErrors(null, data, status, null, {
                                                        hdr: 'Error!',
                                                        msg: 'Failed to get project. GET returned ' +
                                                            'status: ' + status
                                                    });
                                                    return false;
                                                }
                                                else {
                                                    return true;
                                                }
                                        });
                                    }
                                    else {
                                        return false;
                                    }
                            }],
                            InstanceGroupsData: ['$stateParams', 'Rest', 'GetBasePath', 'ProcessErrors',
                                function($stateParams, Rest, GetBasePath, ProcessErrors){
                                    let path = `${GetBasePath('job_templates')}${$stateParams.job_template_id}/instance_groups/`;
                                    Rest.setUrl(path);
                                    return Rest.get()
                                        .then(({data}) => {
                                            if (data.results.length > 0) {
                                                 return data.results;
                                            }
                                        })
                                        .catch(({data, status}) => {
                                            ProcessErrors(null, data, status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get instance groups. GET returned ' +
                                                    'status: ' + status
                                            });
                                    });
                                }],
                            availableLabels: ['Rest', '$stateParams', 'GetBasePath', 'ProcessErrors', 'TemplatesService',
                                function(Rest, $stateParams, GetBasePath, ProcessErrors, TemplatesService) {
                                    return TemplatesService.getAllLabelOptions()
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get labels. GET returned status: ' +
                                                    response.status
                                            });
                                        });
                            }],
                            selectedLabels: ['Rest', '$stateParams', 'GetBasePath', 'TemplatesService', 'ProcessErrors',
                                function(Rest, $stateParams, GetBasePath, TemplatesService, ProcessErrors) {
                                    return TemplatesService.getAllJobTemplateLabels($stateParams.job_template_id)
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get workflow job template labels. GET returned status: ' +
                                                    response.status
                                            });
                                        });
                            }]
                        }
                    }
                });

                addWorkflow = stateDefinitions.generateTree({
                    name: 'templates.addWorkflowJobTemplate',
                    url: '/add_workflow_job_template',
                    modes: ['add'],
                    form: 'WorkflowForm',
                    controllers: {
                        add: 'WorkflowAdd'
                    },
                    resolve: {
                        add: {
                            availableLabels: ['Rest', '$stateParams', 'GetBasePath', 'ProcessErrors', 'TemplatesService',
                                function(Rest, $stateParams, GetBasePath, ProcessErrors, TemplatesService) {
                                    return TemplatesService.getAllLabelOptions()
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get labels. GET returned status: ' +
                                                    response.status
                                            });
                                        });
                            }],
                            checkPermissions: ['Rest', 'GetBasePath', 'TemplatesService', 'Alert', 'ProcessErrors', '$state',
                                function(Rest, GetBasePath, TemplatesService, Alert, ProcessErrors, $state) {
                                    return TemplatesService.getWorkflowJobTemplateOptions()
                                        .then(function(data) {
                                            if (!data.actions.POST) {
                                                $state.go("^");
                                                Alert('Permission Error', 'You do not have permission to add a workflow job template.', 'alert-info');
                                            }
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get workflow job template options. OPTIONS returned status: ' +
                                                    response.status
                                            });
                                        });
                                    }]
                        }
                    }
                });

                editWorkflow = stateDefinitions.generateTree({
                    name: 'templates.editWorkflowJobTemplate',
                    url: '/workflow_job_template/:workflow_job_template_id',
                    modes: ['edit'],
                    form: 'WorkflowForm',
                    controllers: {
                        edit: 'WorkflowEdit'
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'workflow_job_template',
                        activityStreamId: 'workflow_job_template_id'
                    },
                    resolve: {
                        edit: {
                            availableLabels: ['Rest', '$stateParams', 'GetBasePath', 'ProcessErrors', 'TemplatesService',
                                function(Rest, $stateParams, GetBasePath, ProcessErrors, TemplatesService) {
                                    return TemplatesService.getAllLabelOptions()
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get labels. GET returned status: ' +
                                                    response.status
                                            });
                                        });
                            }],
                            selectedLabels: ['Rest', '$stateParams', 'GetBasePath', 'TemplatesService', 'ProcessErrors',
                                function(Rest, $stateParams, GetBasePath, TemplatesService, ProcessErrors) {
                                    return TemplatesService.getAllWorkflowJobTemplateLabels($stateParams.workflow_job_template_id)
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get workflow job template labels. GET returned status: ' +
                                                    response.status
                                            });
                                        });
                            }],
                            workflowJobTemplateData: ['$stateParams', 'TemplatesService', 'ProcessErrors',
                                function($stateParams, TemplatesService, ProcessErrors) {
                                    return TemplatesService.getWorkflowJobTemplate($stateParams.workflow_job_template_id)
                                        .then(function(res) {
                                            return res.data;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: 'Error!',
                                                msg: 'Failed to get workflow job template. GET returned status: ' +
                                                    response.status
                                            });
                                        });
                            }]
                        }
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
                                order_by: 'name',
                                inventory__isnull: false,
                                credential__isnull: false
                            },
                            squash: true,
                            dynamic: true
                        },
                        project_search: {
                            value: {
                                page_size: '5',
                                order_by: 'name'
                            },
                            squash: true,
                            dynamic: true
                        },
                        inventory_source_search: {
                            value: {
                                page_size: '5',
                                not__source: '',
                                order_by: 'name'
                            },
                            squash: true,
                            dynamic: true
                        }
                    },
                    views: {
                        'modal': {
                            template: `<workflow-maker ng-if="includeWorkflowMaker" workflow-job-template-obj="workflow_job_template_obj" can-add-workflow-job-template="canAddWorkflowJobTemplate"></workflow-maker>`
                        },
                        'jobTemplateList@templates.editWorkflowJobTemplate.workflowMaker': {
                            templateProvider: function(WorkflowMakerJobTemplateList, generateList) {

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

                                        $scope.$watch('job_templates', function(){
                                            if($scope.selectedTemplate){
                                                $scope.job_templates.forEach(function(row, i) {
                                                    if(row.id === $scope.selectedTemplate.id) {
                                                        $scope.job_templates[i].checked = 1;
                                                    }
                                                    else {
                                                        $scope.job_templates[i].checked = 0;
                                                    }
                                                });
                                            }
                                        });
                                    }

                                    $scope.toggle_row = function(selectedRow) {

                                        $scope.job_templates.forEach(function(row, i) {
                                            if (row.id === selectedRow.id) {
                                                $scope.job_templates[i].checked = 1;
                                                $scope.selection[list.iterator] = {
                                                    id: row.id,
                                                    name: row.name
                                                };

                                                $scope.templateSelected(row);
                                            }
                                        });

                                    };

                                    $scope.$on('templateSelected', function(e, options) {
                                        if(options.activeTab !== 'jobs') {
                                            $scope.job_templates.forEach(function(row, i) {
                                                $scope.job_templates[i].checked = 0;
                                            });
                                        }
                                        else {
                                            if($scope.selectedTemplate){
                                                $scope.job_templates.forEach(function(row, i) {
                                                    if(row.id === $scope.selectedTemplate.id) {
                                                        $scope.job_templates[i].checked = 1;
                                                    }
                                                    else {
                                                        $scope.job_templates[i].checked = 0;
                                                    }
                                                });
                                            }
                                        }
                                    });

                                    $scope.$on('clearWorkflowLists', function() {
                                        $scope.job_templates.forEach(function(row, i) {
                                            $scope.job_templates[i].checked = 0;
                                        });
                                    });
                                }
                            ]
                        },
                        'inventorySyncList@templates.editWorkflowJobTemplate.workflowMaker': {
                            templateProvider: function(WorkflowInventorySourcesList, generateList) {
                                let html = generateList.build({
                                    list: WorkflowInventorySourcesList,
                                    input_type: 'radio',
                                    mode: 'lookup'
                                });
                                return html;
                            },
                            // encapsulated $scope in this controller will be a initialized as child of 'modal' $scope, because of element hierarchy
                            controller: ['$scope', 'WorkflowInventorySourcesList', 'InventorySourcesDataset',
                                function($scope, list, Dataset) {

                                    init();

                                    function init() {
                                        $scope.list = list;
                                        $scope[`${list.iterator}_dataset`] = Dataset.data;
                                        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

                                        $scope.$watch('workflow_inventory_sources', function(){
                                            if($scope.selectedTemplate){
                                                $scope.workflow_inventory_sources.forEach(function(row, i) {
                                                    if(row.id === $scope.selectedTemplate.id) {
                                                        $scope.workflow_inventory_sources[i].checked = 1;
                                                    }
                                                    else {
                                                        $scope.workflow_inventory_sources[i].checked = 0;
                                                    }
                                                });
                                            }
                                        });
                                    }

                                    $scope.toggle_row = function(selectedRow) {

                                        $scope.workflow_inventory_sources.forEach(function(row, i) {
                                            if (row.id === selectedRow.id) {
                                                $scope.workflow_inventory_sources[i].checked = 1;
                                                $scope.selection[list.iterator] = {
                                                    id: row.id,
                                                    name: row.name
                                                };

                                                $scope.templateSelected(row);
                                            }
                                        });

                                    };

                                    $scope.$on('templateSelected', function(e, options) {
                                        if(options.activeTab !== 'inventory_sync') {
                                            $scope.workflow_inventory_sources.forEach(function(row, i) {
                                                $scope.workflow_inventory_sources[i].checked = 0;
                                            });
                                        }
                                        else {
                                            if($scope.selectedTemplate){
                                                $scope.workflow_inventory_sources.forEach(function(row, i) {
                                                    if(row.id === $scope.selectedTemplate.id) {
                                                        $scope.workflow_inventory_sources[i].checked = 1;
                                                    }
                                                    else {
                                                        $scope.workflow_inventory_sources[i].checked = 0;
                                                    }
                                                });
                                            }
                                        }
                                    });

                                    $scope.$on('clearWorkflowLists', function() {
                                        $scope.workflow_inventory_sources.forEach(function(row, i) {
                                            $scope.workflow_inventory_sources[i].checked = 0;
                                        });
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

                                        $scope.$watch('projects', function(){
                                            if($scope.selectedTemplate){
                                                $scope.projects.forEach(function(row, i) {
                                                    if(row.id === $scope.selectedTemplate.id) {
                                                        $scope.projects[i].checked = 1;
                                                    }
                                                    else {
                                                        $scope.projects[i].checked = 0;
                                                    }
                                                });
                                            }
                                        });
                                    }

                                    $scope.toggle_row = function(selectedRow) {

                                        $scope.projects.forEach(function(row, i) {
                                            if (row.id === selectedRow.id) {
                                                $scope.projects[i].checked = 1;
                                                $scope.selection[list.iterator] = {
                                                    id: row.id,
                                                    name: row.name
                                                };

                                                $scope.templateSelected(row);
                                            }
                                        });

                                    };

                                    $scope.$on('templateSelected', function(e, options) {
                                        if(options.activeTab !== 'project_sync') {
                                            $scope.projects.forEach(function(row, i) {
                                                $scope.projects[i].checked = 0;
                                            });
                                        }
                                        else {
                                            if($scope.selectedTemplate){
                                                $scope.projects.forEach(function(row, i) {
                                                    if(row.id === $scope.selectedTemplate.id) {
                                                        $scope.projects[i].checked = 1;
                                                    }
                                                    else {
                                                        $scope.projects[i].checked = 0;
                                                    }
                                                });
                                            }
                                        }
                                    });

                                    $scope.$on('clearWorkflowLists', function() {
                                        $scope.projects.forEach(function(row, i) {
                                            $scope.projects[i].checked = 0;
                                        });
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
                            },
                            controller: ['$scope', '$timeout', 'CreateSelect2',
                                function($scope, $timeout, CreateSelect2) {
                                    function resetPromptFields() {
                                        $scope.credential = null;
                                        $scope.credential_name = null;
                                        $scope.inventory = null;
                                        $scope.inventory_name = null;
                                        $scope.job_type = null;
                                        $scope.limit = null;
                                        $scope.job_tags = null;
                                        $scope.skip_tags = null;
                                    }

                                    $scope.saveNodeForm = function(){
                                        // Gather up all of our form data - then let the main scope know what
                                        // the new data is

                                        $scope.confirmNodeForm({
                                            skip_tags: $scope.skip_tags,
                                            job_tags: $scope.job_tags,
                                            limit: $scope.limit,
                                            credential: $scope.credential,
                                            credential_name: $scope.credential_name,
                                            inventory: $scope.inventory,
                                            inventory_name: $scope.inventory_name,
                                            edgeType: $scope.edgeType,
                                            job_type: $scope.job_type
                                        });
                                    };

                                    $scope.$on('templateSelected', function(e, options) {

                                        resetPromptFields();
                                        // Loop across the preset values and attach them to scope
                                        _.forOwn(options.presetValues, function(value, key) {
                                            $scope[key] = value;
                                        });

                                        // The default needs to be in place before we can select2-ify the dropdown
                                        $timeout(function() {
                                            CreateSelect2({
                                                element: '#workflow_maker_job_type',
                                                multiple: false
                                            });
                                        });
                                    });

                                    $scope.$on('setEdgeType', function(e, edgeType) {
                                        $scope.edgeType = edgeType;
                                    });
                                }
                            ]
                        }
                    },
                    resolve: {
                        JobTemplateDataset: ['WorkflowMakerJobTemplateList', 'QuerySet', '$stateParams', 'GetBasePath',
                            (list, qs, $stateParams, GetBasePath) => {
                                let path = GetBasePath(list.basePath);
                                return qs.search(path, $stateParams[`${list.iterator}_search`]);
                            }
                        ],
                        ProjectDataset: ['WorkflowProjectList', 'QuerySet', '$stateParams', 'GetBasePath',
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
                        WorkflowMakerJobTemplateList: ['TemplateList',
                            (TemplateList) => {
                                let list = _.cloneDeep(TemplateList);
                                delete list.actions;
                                delete list.fields.type;
                                delete list.fields.description;
                                delete list.fields.smart_status;
                                delete list.fields.labels;
                                delete list.fieldActions;
                                list.fields.name.columnClass = "col-md-8";
                                list.iterator = 'job_template';
                                list.name = 'job_templates';
                                list.basePath = "job_templates";
                                list.fields.info = {
                                    ngInclude: "'/static/partials/job-template-details.html'",
                                    type: 'template',
                                    columnClass: 'col-md-3',
                                    label: '',
                                    nosort: true
                                };
                                list.maxVisiblePages = 5;
                                list.searchBarFullWidth = true;

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
                                list.maxVisiblePages = 5;
                                list.searchBarFullWidth = true;

                                return list;
                            }
                        ],
                        WorkflowInventorySourcesList: ['InventorySourcesList',
                            (InventorySourcesList) => {
                                let list = _.cloneDeep(InventorySourcesList);
                                list.maxVisiblePages = 5;
                                list.searchBarFullWidth = true;

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
                        ListDefinition: ['InventoryList', function(InventoryList) {
                            // mutate the provided list definition here
                            let list = _.cloneDeep(InventoryList);
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
                    addJobTemplate,
                    editJobTemplate,
                    addWorkflow,
                    editWorkflow
                ]).then((generated) => {
                    return {
                        states: _.reduce(generated, (result, definition) => {
                            return result.concat(definition.states);
                        }, [
                            stateExtender.buildDefinition(templatesListRoute),
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
