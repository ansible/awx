/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import { templateUrl } from '../shared/template-url/template-url.factory';

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

                workflowMaker = stateExtender.buildDefinition({
                    name: 'templates.editWorkflowJobTemplate.workflowMaker',
                    url: '/workflow-maker',
                    views: {
                        'modal': {
                            template: ` <workflow-maker ng-if="includeWorkflowMaker" tree-data="workflowTree"></workflow-maker>`
                        },
                        // 'jobsTemplateList@templates.editWorkflowJobTemplate.workflowMaker': {
                        //     templateProvider: function(JobTemplateList, generateList) {
                        //         let html = generateList.build({
                        //             list: JobTemplateList,
                        //             mode: 'edit'
                        //         });
                        //         return html;
                        //     }
                        // },
                        // 'inventorySyncList@templates.editWorkflowJobTemplate.workflowMaker': {
                        //     templateProvider: function(InventoryList, generateList) {
                        //         let html = generateList.build({
                        //             list: InventoryList,
                        //             mode: 'edit'
                        //         });
                        //         return html;
                        //     }
                        // },
                        // 'projectList@templates.editWorkflowJobTemplate.workflowMaker': {
                        //     templateProvider: function(ProjectList, generateList) {
                        //         let html = generateList.build({
                        //             list: ProjectList,
                        //             mode: 'edit'
                        //         });
                        //         return html;
                        //     }
                        // },
                        'workflowForm@templates.editWorkflowJobTemplate.workflowMaker': {
                            templateProvider: function(WorkflowMakerForm, GenerateForm) {
                                let form = WorkflowMakerForm();
                                let html = GenerateForm.buildHTML(form, {
                                    mode: 'add',
                                    related: false,
                                });
                                return html;
                            }
                        }
                    }
                });

                inventoryLookup = stateExtender.buildDefinition({
                    searchPrefix: 'inventory',
                    //squashSearchUrl: true, @issue enable
                    name: 'templates.editWorkflowJobTemplate.workflowMaker.inventory',
                    url: '/inventory',
                    data: {
                        lookup: true
                    },
                    params: {
                        inventory_search: {
                            value: { page_size: '5'}
                        }
                    },
                    views: {
                        'related': {
                            templateProvider: function(InventoryList, generateList) {
                                let list_html = generateList.build({
                                    mode: 'lookup',
                                    list: InventoryList,
                                    input_type: 'radio'
                                });
                                return `<lookup-modal>${list_html}</lookup-modal>`;

                            }
                        }
                    },
                    resolve: {
                        ListDefinition: ['InventoryList', function(list) {
                            return list;
                        }],
                        Dataset: ['InventoryList', 'QuerySet', '$stateParams', 'GetBasePath',
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
                });




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
                            workflowMaker,
                            inventoryLookup
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
