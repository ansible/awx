/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import templatesService from './templates.service';
import surveyMaker from './survey-maker/main';
import jobTemplates from './job_templates/main';
import workflowAdd from './workflows/add-workflow/main';
import workflowEdit from './workflows/edit-workflow/main';
import labels from './labels/main';
import prompt from './prompt/main';
import workflowChart from './workflows/workflow-chart/main';
import workflowKey from './workflows/workflow-key/main';
import workflowMaker from './workflows/workflow-maker/main';
import workflowControls from './workflows/workflow-controls/main';
import WorkflowForm from './workflows.form';
import InventorySourcesList from './inventory-sources.list';
import TemplateList from './templates.list';
import listRoute from '~features/templates/routes/templatesList.route.js';
import templateCompletedJobsRoute from '~features/jobs/routes/templateCompletedJobs.route.js';
import workflowJobTemplateCompletedJobsRoute from '~features/jobs/routes/workflowJobTemplateCompletedJobs.route.js';
import {
    jobTemplatesSchedulesListRoute,
    jobTemplatesSchedulesAddRoute,
    jobTemplatesSchedulesEditRoute,
    workflowSchedulesRoute,
    workflowSchedulesAddRoute,
    workflowSchedulesEditRoute
} from '../scheduler/schedules.route';

export default
angular.module('templates', [surveyMaker.name, jobTemplates.name, labels.name, prompt.name, workflowAdd.name, workflowEdit.name,
        workflowChart.name, workflowKey.name, workflowMaker.name, workflowControls.name
    ])
    .service('TemplatesService', templatesService)
    .factory('WorkflowForm', WorkflowForm)
    // TODO: currently being kept arround for rbac selection, templates within projects and orgs, etc.
    .factory('TemplateList', TemplateList)
    .value('InventorySourcesList', InventorySourcesList)
    .config(['$stateProvider', 'stateDefinitionsProvider', '$stateExtenderProvider',
        function($stateProvider, stateDefinitionsProvider, $stateExtenderProvider) {
            let stateTree, addJobTemplate, editJobTemplate, addWorkflow, editWorkflow,
                workflowMaker,
                stateDefinitions = stateDefinitionsProvider.$get(),
                stateExtender = $stateExtenderProvider.$get();

            function generateStateTree() {

                addJobTemplate = stateDefinitions.generateTree({
                    name: 'templates.addJobTemplate',
                    url: '/add_job_template?inventory_id&credential_id&project_id',
                    modes: ['add'],
                    form: 'JobTemplateForm',
                    controllers: {
                        add: 'JobTemplateAdd'
                    },
                    resolve: {
                        add: {
                            Inventory: ['$stateParams', 'Rest', 'GetBasePath', 'ProcessErrors', 'i18n',
                                function($stateParams, Rest, GetBasePath, ProcessErrors, i18n){
                                    if($stateParams.inventory_id){
                                        let path = `${GetBasePath('inventory')}${$stateParams.inventory_id}`;
                                        Rest.setUrl(path);
                                        return Rest.get().
                                            then(function(data){
                                                return data.data;
                                            }).catch(function(response) {
                                                ProcessErrors(null, response.data, response.status, null, {
                                                    hdr: i18n._('Error!'),
                                                    msg: i18n._('Failed to get inventory info. GET returned status: ') +
                                                        response.status
                                                });
                                            });
                                    }
                            }],
                            Project: ['Rest', 'GetBasePath', 'ProcessErrors', '$transition$', 'i18n',
                                function(Rest, GetBasePath, ProcessErrors, $transition$, i18n){
                                    if($transition$.params().credential_id){
                                        let path = `${GetBasePath('projects')}?credential__id=${Number($transition$.params().credential_id)}`;
                                        Rest.setUrl(path);
                                        return Rest.get().
                                            then(function(data){
                                                return data.data.results[0];
                                            }).catch(function(response) {
                                                ProcessErrors(null, response.data, response.status, null, {
                                                    hdr: i18n._('Error!'),
                                                    msg: i18n._('Failed to get project info. GET returned status: ') +
                                                        response.status
                                                });
                                            });
                                    }
                                    else if($transition$.params().project_id){
                                        let path = `${GetBasePath('projects')}${$transition$.params().project_id}`;
                                        Rest.setUrl(path);
                                        return Rest.get().
                                            then(function(data){
                                                return data.data;
                                            }).catch(function(response) {
                                                ProcessErrors(null, response.data, response.status, null, {
                                                    hdr: i18n._('Error!'),
                                                    msg: i18n._('Failed to get project info. GET returned status: ') +
                                                        response.status
                                                });
                                            });
                                    }
                            }],
                            availableLabels: ['ProcessErrors', 'TemplatesService', 'i18n',
                                function(ProcessErrors, TemplatesService, i18n) {
                                    return TemplatesService.getAllLabelOptions()
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get labels. GET returned status: ') +
                                                    response.status
                                            });
                                        });
                            }],
                            checkPermissions: ['TemplatesService', 'Alert', 'ProcessErrors', '$state', 'i18n',
                                function(TemplatesService, Alert, ProcessErrors, $state, i18n) {
                                    return TemplatesService.getJobTemplateOptions()
                                        .then(function(data) {
                                            if (!data.actions.POST) {
                                                $state.go("^");
                                                Alert(i18n._('Permission Error'), i18n._('You do not have permission to add a job template, or there are no projects available.'), 'alert-info');
                                            }
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get job template options. OPTIONS returned status: ') +
                                                    response.status
                                            });
                                        });
                            }],
                            ConfigData: ['ConfigService', 'ProcessErrors', 'i18n', (ConfigService, ProcessErrors, i18n) => {
                                return ConfigService.getConfig()
                                    .then(response => response)
                                    .catch(({data, status}) => {
                                        ProcessErrors(null, data, status, null, {
                                            hdr: i18n._('Error!'),
                                            msg: i18n._('Failed to get config. GET returned status: ') + status
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
                        edit: 'JobTemplateEdit'
                    },
                    data: {
                        activityStream: true,
                        activityStreamTarget: 'job_template',
                        activityStreamId: 'job_template_id'
                    },
                    breadcrumbs: {
                        edit: '{{breadcrumb.job_template_name}}'
                    },
                    resolve: {
                        edit: {
                            jobTemplateData: ['$stateParams', 'TemplatesService', 'ProcessErrors', 'i18n',
                                function($stateParams, TemplatesService, ProcessErrors, i18n) {
                                    return TemplatesService.getJobTemplate($stateParams.job_template_id)
                                        .then(function(res) {
                                            return res.data;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get job template. GET returned status: ') +
                                                    response.status
                                            });
                                        });
                            }],
                            projectGetPermissionDenied: ['Rest', 'ProcessErrors', 'jobTemplateData', 'i18n',
                                function(Rest, ProcessErrors, jobTemplateData, i18n) {
                                    if(jobTemplateData.related.project) {
                                        Rest.setUrl(jobTemplateData.related.project);
                                        return Rest.get()
                                            .then(() => {
                                                return false;
                                            })
                                            .catch(({data, status}) => {
                                                if (status !== 403) {
                                                    ProcessErrors(null, data, status, null, {
                                                        hdr: i18n._('Error!'),
                                                        msg: i18n._('Failed to get project. GET returned status: ') + status
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
                            inventoryGetPermissionDenied: ['Rest', 'ProcessErrors', 'jobTemplateData', 'i18n',
                                function(Rest, ProcessErrors, jobTemplateData, i18n) {
                                    if(jobTemplateData.related.inventory) {
                                        Rest.setUrl(jobTemplateData.related.inventory);
                                        return Rest.get()
                                            .then(() => {
                                                return false;
                                            })
                                            .catch(({data, status}) => {
                                                if (status !== 403) {
                                                    ProcessErrors(null, data, status, null, {
                                                        hdr: i18n._('Error!'),
                                                        msg: i18n._('Failed to get project. GET returned status: ') + status
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
                            InstanceGroupsData: ['$stateParams', 'Rest', 'GetBasePath', 'ProcessErrors', 'i18n',
                                function($stateParams, Rest, GetBasePath, ProcessErrors, i18n){
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
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get instance groups. GET returned status: ') + status
                                            });
                                    });
                                }],
                            availableLabels: ['ProcessErrors', 'TemplatesService', 'i18n',
                                function(ProcessErrors, TemplatesService, i18n) {
                                    return TemplatesService.getAllLabelOptions()
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get labels. GET returned status: ') +
                                                    response.status
                                            });
                                        });
                            }],
                            selectedLabels: ['$stateParams', 'TemplatesService', 'ProcessErrors', 'i18n',
                                function($stateParams, TemplatesService, ProcessErrors, i18n) {
                                    return TemplatesService.getAllJobTemplateLabels($stateParams.job_template_id)
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get workflow job template labels. GET returned status: ') +
                                                    response.status
                                            });
                                        });
                            }],
                            ConfigData: ['ConfigService', 'ProcessErrors', 'i18n', (ConfigService, ProcessErrors, i18n) => {
                                return ConfigService.getConfig()
                                    .then(response => response)
                                    .catch(({data, status}) => {
                                        ProcessErrors(null, data, status, null, {
                                            hdr: i18n._('Error!'),
                                            msg: i18n._('Failed to get config. GET returned status: ') + status
                                        });
                                    });
                            }],
                            isNotificationAdmin: ['Rest', 'ProcessErrors', 'GetBasePath', 'i18n',
                                function(Rest, ProcessErrors, GetBasePath, i18n) {
                                    Rest.setUrl(`${GetBasePath('organizations')}?role_level=notification_admin_role&page_size=1`);
                                    return Rest.get()
                                        .then(({data}) => {
                                            return data.count > 0;
                                        })
                                        .catch(({data, status}) => {
                                            ProcessErrors(null, data, status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get organizations for which this user is a notification administrator. GET returned ') + status
                                            });
                                    });
                            }],
                            webhookKey: ['Rest', 'ProcessErrors', 'jobTemplateData', 'i18n',
                                function(Rest, ProcessErrors, jobTemplateData, i18n) {
                                    Rest.setUrl(jobTemplateData.related.webhook_key);
                                    return Rest.get()
                                        .then(({ data = {} }) => {
                                            return data.webhook_key || '';
                                        })
                                        .catch(({data, status}) => {
                                            if (status === 403) {
                                                return;
                                            }
                                            ProcessErrors(null, data, status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get webhook key GET returned ') + status
                                            });
                                    });
                            }],
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
                            Inventory: ['$stateParams', 'Rest', 'GetBasePath', 'ProcessErrors', 'i18n',
                                function($stateParams, Rest, GetBasePath, ProcessErrors, i18n){
                                    if($stateParams.inventory_id){
                                        let path = `${GetBasePath('inventory')}${$stateParams.inventory_id}`;
                                        Rest.setUrl(path);
                                        return Rest.get().
                                            then(function(data){
                                                return data.data;
                                            }).catch(function(response) {
                                                ProcessErrors(null, response.data, response.status, null, {
                                                    hdr: i18n._('Error!'),
                                                    msg: i18n._('Failed to get inventory info. GET returned status: ') +
                                                        response.status
                                                });
                                            });
                                    }
                            }],
                            availableLabels: ['ProcessErrors', 'TemplatesService', 'i18n',
                                function(ProcessErrors, TemplatesService, i18n) {
                                    return TemplatesService.getAllLabelOptions()
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get labels. GET returned status: ') +
                                                    response.status
                                            });
                                        });
                            }],
                            checkPermissions: ['TemplatesService', 'Alert', 'ProcessErrors', '$state', 'i18n',
                                function(TemplatesService, Alert, ProcessErrors, $state, i18n) {
                                    return TemplatesService.getWorkflowJobTemplateOptions()
                                        .then(function(data) {
                                            if (!data.actions.POST) {
                                                $state.go("^");
                                                Alert(i18n._('Permission Error'), i18n._('You do not have permission to add a workflow job template.'), 'alert-info');
                                            }
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get workflow job template options. OPTIONS returned status: ') +
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
                    breadcrumbs: {
                        edit: '{{breadcrumb.workflow_job_template_name}}'
                    },
                    resolve: {
                        edit: {
                            Inventory: ['$stateParams', 'Rest', 'GetBasePath', 'ProcessErrors', 'i18n',
                                function($stateParams, Rest, GetBasePath, ProcessErrors, i18n){
                                    if($stateParams.inventory_id){
                                        let path = `${GetBasePath('inventory')}${$stateParams.inventory_id}`;
                                        Rest.setUrl(path);
                                        return Rest.get().
                                            then(function(data){
                                                return data.data;
                                            }).catch(function(response) {
                                                ProcessErrors(null, response.data, response.status, null, {
                                                    hdr: i18n._('Error!'),
                                                    msg: i18n._('Failed to get inventory info. GET returned status: ') +
                                                        response.status
                                                });
                                            });
                                    }
                            }],
                            availableLabels: ['ProcessErrors', 'TemplatesService', 'i18n',
                                function(ProcessErrors, TemplatesService, i18n) {
                                    return TemplatesService.getAllLabelOptions()
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get labels. GET returned status: ') +
                                                    response.status
                                            });
                                        });
                            }],
                            selectedLabels: ['$stateParams', 'TemplatesService', 'ProcessErrors', 'i18n',
                                function($stateParams, TemplatesService, ProcessErrors, i18n) {
                                    return TemplatesService.getAllWorkflowJobTemplateLabels($stateParams.workflow_job_template_id)
                                        .then(function(labels){
                                            return labels;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get workflow job template labels. GET returned status: ') +
                                                    response.status
                                            });
                                        });
                            }],
                            workflowJobTemplateData: ['$stateParams', 'TemplatesService', 'ProcessErrors', 'i18n',
                                function($stateParams, TemplatesService, ProcessErrors, i18n) {
                                    return TemplatesService.getWorkflowJobTemplate($stateParams.workflow_job_template_id)
                                        .then(function(res) {
                                            return res.data;
                                        }).catch(function(response){
                                            ProcessErrors(null, response.data, response.status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get workflow job template. GET returned status: ') +
                                                    response.status
                                            });
                                        });
                            }],
                            workflowLaunch: ['$stateParams', 'WorkflowJobTemplateModel',
                                function($stateParams, WorkflowJobTemplate) {
                                    let workflowJobTemplate = new WorkflowJobTemplate();

                                    return workflowJobTemplate.getLaunch($stateParams.workflow_job_template_id)
                                        .then(({data}) => {
                                            return data;
                                        });
                            }],
                            isNotificationAdmin: ['Rest', 'ProcessErrors', 'GetBasePath', 'i18n',
                                function(Rest, ProcessErrors, GetBasePath, i18n) {
                                    Rest.setUrl(`${GetBasePath('organizations')}?role_level=notification_admin_role&page_size=1`);
                                    return Rest.get()
                                        .then(({data}) => {
                                            return data.count > 0;
                                        })
                                        .catch(({data, status}) => {
                                            ProcessErrors(null, data, status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get organizations for which this user is a notification administrator. GET returned ') + status
                                            });
                                    });
                            }],
                            webhookKey: ['Rest', 'ProcessErrors', 'workflowJobTemplateData', 'i18n',
                                function(Rest, ProcessErrors, workflowJobTemplateData, i18n) {
                                    Rest.setUrl(workflowJobTemplateData.related.webhook_key);
                                    return Rest.get()
                                        .then(({ data = {} }) => {
                                            return data.webhook_key || '';
                                        })
                                        .catch(({data, status}) => {
                                            if (status === 403) {
                                                return;
                                            }
                                            ProcessErrors(null, data, status, null, {
                                                hdr: i18n._('Error!'),
                                                msg: i18n._('Failed to get webhook key GET returned ') + status
                                            });
                                    });
                            }],
                        }
                    }
                });

                workflowMaker = {
                    name: 'templates.editWorkflowJobTemplate.workflowMaker',
                    url: '/workflow-maker',
                    data: {
                        formChildState: true
                    },
                    params: {
                        wf_maker_template_search: {
                            value: {
                                order_by: 'name',
                                page_size: '10',
                                role_level: 'execute_role',
                                type: 'workflow_job_template,job_template'
                            },
                            squash: false,
                            dynamic: true
                        },
                        wf_maker_project_search: {
                            value: {
                                order_by: 'name',
                                page_size: '10'
                            },
                            squash: true,
                            dynamic: true
                        },
                        wf_maker_inventory_source_search: {
                            value: {
                                not__source: '',
                                order_by: 'name',
                                page_size: '10'
                            },
                            squash: true,
                            dynamic: true
                        }
                    },
                    views: {
                        'modal': {
                            template: `<workflow-maker ng-if="includeWorkflowMaker" workflow-job-template-obj="workflow_job_template_obj" can-add-or-edit="canAddOrEdit"></workflow-maker>`
                        }
                    }
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
                            stateExtender.buildDefinition(listRoute),
                            stateExtender.buildDefinition(templateCompletedJobsRoute),
                            stateExtender.buildDefinition(workflowJobTemplateCompletedJobsRoute),
                            stateExtender.buildDefinition(workflowMaker),
                            stateExtender.buildDefinition(jobTemplatesSchedulesListRoute),
                            stateExtender.buildDefinition(jobTemplatesSchedulesAddRoute),
                            stateExtender.buildDefinition(jobTemplatesSchedulesEditRoute),
                            stateExtender.buildDefinition(workflowSchedulesRoute),
                            stateExtender.buildDefinition(workflowSchedulesAddRoute),
                            stateExtender.buildDefinition(workflowSchedulesEditRoute)
                        ])
                    };
                });
            }

            stateTree = {
                name: 'templates.**',
                url: '/templates',
                lazyLoad: () => generateStateTree()
            };

            $stateProvider.state(stateTree);

        }
    ]);