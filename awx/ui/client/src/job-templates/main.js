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
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider ) {
            let stateTree, addJobTemplate, editJobTemplate, addWorkflow, editWorkflow,
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
                            stateExtender.buildDefinition(jobTemplatesListRoute)

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
