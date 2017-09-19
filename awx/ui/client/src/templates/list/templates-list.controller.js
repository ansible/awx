/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope',
    'Alert','TemplateList', 'Prompt', 'ProcessErrors',
    'GetBasePath', 'InitiatePlaybookRun', 'Wait', '$state', '$filter',
    'Dataset', 'rbacUiControlService', 'TemplatesService','QuerySet',
    'TemplateCopyService', 'i18n',
    function(
        $scope, $rootScope, Alert,
        TemplateList, Prompt, ProcessErrors, GetBasePath,
        InitiatePlaybookRun, Wait, $state, $filter, Dataset, rbacUiControlService, TemplatesService,
        qs, TemplateCopyService, i18n
    ) {

        var list = TemplateList;

        init();

        function init() {
            $scope.canAdd = false;

            rbacUiControlService.canAdd("job_templates")
                .then(function(params) {
                    $scope.canAddJobTemplate = params.canAdd;
                });

            rbacUiControlService.canAdd("workflow_job_templates")
                .then(function(params) {
                    $scope.canAddWorkflowJobTemplate = params.canAdd;
                });
            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            $scope.options = {};

            $rootScope.flashMessage = null;
        }

        $scope.$on(`${list.iterator}_options`, function(event, data){
            $scope.options = data.data.actions.GET;
            optionsRequestDataProcessing();
        });

        $scope.$watchCollection('templates', function() {
                optionsRequestDataProcessing();
            }
        );
        // iterate over the list and add fields like type label, after the
        // OPTIONS request returns, or the list is sorted/paginated/searched
        function optionsRequestDataProcessing(){
            $scope[list.name].forEach(function(item, item_idx) {
                var itm = $scope[list.name][item_idx];

                // Set the item type label
                if (list.fields.type && $scope.options.hasOwnProperty('type')) {
                    $scope.options.type.choices.forEach(function(choice) {
                        if (choice[0] === item.type) {
                            itm.type_label = choice[1];
                        }
                    });
                }
            });
        }


        $scope.$on(`ws-jobs`, function () {
            let path = GetBasePath(list.basePath) || GetBasePath(list.name);
            qs.search(path, $state.params[`${list.iterator}_search`])
            .then(function(searchResponse) {
                $scope[`${list.iterator}_dataset`] = searchResponse.data;
                $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            });
        });

        $scope.editJobTemplate = function(template) {
            if(template) {
                    if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                        $state.transitionTo('templates.editJobTemplate', {job_template_id: template.id});
                    }
                    else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                        $state.transitionTo('templates.editWorkflowJobTemplate', {workflow_job_template_id: template.id});
                    }
                    else {
                        // Something went wrong - Let the user know that we're unable to launch because we don't know
                        // what type of job template this is
                        Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while routing to edit.');
                    }
                }
            else {
                Alert('Error: Unable to edit template', 'Template parameter is missing');
            }
        };

        $scope.deleteJobTemplate = function(template) {
           if(template) {
                    Prompt({
                        hdr: i18n._('Delete'),
                        body: `<div class="Prompt-bodyQuery">${i18n._("Are you sure you want to delete the template below?")}</div><div class="Prompt-bodyTarget">${$filter('sanitize')(template.name)}</div>`,
                        action: function() {

                            function handleSuccessfulDelete(isWorkflow) {
                                let stateParamId = isWorkflow ? $state.params.workflow_job_template_id : $state.params.job_template_id;

                                let reloadListStateParams = null;

                                if($scope.templates.length === 1 && $state.params.template_search && !_.isEmpty($state.params.template_search.page) && $state.params.template_search.page !== '1') {
                                    reloadListStateParams = _.cloneDeep($state.params);
                                    reloadListStateParams.template_search.page = (parseInt(reloadListStateParams.template_search.page)-1).toString();
                                }

                                if (parseInt(stateParamId) === template.id) {
                                    // Move the user back to the templates list
                                    $state.go("templates", reloadListStateParams, {reload: true});
                                } else {
                                    $state.go(".", reloadListStateParams, {reload: true});
                                }
                                Wait('stop');
                            }

                            $('#prompt-modal').modal('hide');
                            Wait('start');
                            if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                                TemplatesService.deleteWorkflowJobTemplate(template.id)
                                .then(function () {
                                    handleSuccessfulDelete(true);
                                })
                                .catch(function (response) {
                                    Wait('stop');
                                    ProcessErrors($scope, response.data, response.status, null, { hdr: 'Error!',
                                        msg: 'Call to delete workflow job template failed. DELETE returned status: ' + response.status + '.'});
                                });
                            }
                            else if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                                TemplatesService.deleteJobTemplate(template.id)
                                .then(function () {
                                    handleSuccessfulDelete();
                                })
                                .catch(function (response) {
                                    Wait('stop');
                                    ProcessErrors($scope, response.data, response.status, null, { hdr: 'Error!',
                                        msg: 'Call to delete job template failed. DELETE returned status: ' + response.status + '.'});
                                });
                            }
                            else {
                                Wait('stop');
                                Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while deleting.');
                            }
                        },
                        actionText: i18n._('DELETE')
                    });
                }
                else {
                    Alert('Error: Unable to delete template', 'Template parameter is missing');
                }
        };

        $scope.submitJob = function(template) {
            if(template) {
                    if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                        InitiatePlaybookRun({ scope: $scope, id: template.id, job_type: 'job_template' });
                    }
                    else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                        InitiatePlaybookRun({ scope: $scope, id: template.id, job_type: 'workflow_job_template' });
                    }
                    else {
                        // Something went wrong - Let the user know that we're unable to launch because we don't know
                        // what type of job template this is
                        Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while launching.');
                    }
                }
                else {
                    Alert('Error: Unable to launch template', 'Template parameter is missing');
                }
        };

        $scope.scheduleJob = function(template) {
            if(template) {
                    if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                        $state.go('jobTemplateSchedules', {id: template.id});
                    }
                    else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                        $state.go('workflowJobTemplateSchedules', {id: template.id});
                    }
                    else {
                        // Something went wrong - Let the user know that we're unable to redirect to schedule because we don't know
                        // what type of job template this is
                        Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while routing to schedule.');
                    }
                }
                else {
                    Alert('Error: Unable to schedule job', 'Template parameter is missing');
                }
        };

        $scope.copyTemplate = function(template) {
            if(template) {
                if(template.type && template.type === 'job_template') {
                    Wait('start');
         			TemplateCopyService.get(template.id)
         			.success(function(res){
         					TemplateCopyService.set(res)
                            .success(function(res){
                                Wait('stop');
                                if(res.type && res.type === 'job_template') {
                                    $state.go('templates.editJobTemplate', {job_template_id: res.id}, {reload: true});
                                }
                            });
         			})
          			.error(function(res, status){
                        ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
                        msg: 'Call failed. Return status: '+ status});
                    });
                }
                else if(template.type && template.type === 'workflow_job_template') {
                    TemplateCopyService.getWorkflowCopy(template.id)
                    .then(function(result) {

                        if(result.data.can_copy) {
                            if(result.data.can_copy_without_user_input) {
                                // Go ahead and copy the workflow - the user has full priveleges on all the resources
                                TemplateCopyService.copyWorkflow(template.id)
                                .then(function(result) {
                                    $state.go('templates.editWorkflowJobTemplate', {workflow_job_template_id: result.data.id}, {reload: true});
                                })
                                .catch(function (response) {
                                    Wait('stop');
                                    ProcessErrors($scope, response.data, response.status, null, { hdr: 'Error!',
                                        msg: 'Call to copy workflow job template failed. Return status: ' + response.status + '.'});
                                });
                            }
                            else {

                                let bodyHtml = `
                                    <div class="Prompt-bodyQuery">
                                        You do not have access to all resources used by this workflow.  Resources that you don\'t have access to will not be copied and will result in an incomplete workflow.
                                    </div>
                                    <div class="Prompt-bodyTarget">`;

                                        // List the unified job templates user can not access
                                        if (result.data.templates_unable_to_copy.length > 0) {
                                            bodyHtml += '<div>Unified Job Templates that can not be copied<ul>';
                                            _.forOwn(result.data.templates_unable_to_copy, function(ujt) {
                                                if(ujt) {
                                                    bodyHtml += '<li>' + ujt + '</li>';
                                                }
                                            });
                                            bodyHtml += '</ul></div>';
                                        }
                                        // List the prompted inventories user can not access
                                        if (result.data.inventories_unable_to_copy.length > 0) {
                                            bodyHtml += '<div>Node prompted inventories that can not be copied<ul>';
                                            _.forOwn(result.data.inventories_unable_to_copy, function(inv) {
                                                if(inv) {
                                                    bodyHtml += '<li>' + inv + '</li>';
                                                }
                                            });
                                            bodyHtml += '</ul></div>';
                                        }
                                        // List the prompted credentials user can not access
                                        if (result.data.credentials_unable_to_copy.length > 0) {
                                            bodyHtml += '<div>Node prompted credentials that can not be copied<ul>';
                                            _.forOwn(result.data.credentials_unable_to_copy, function(cred) {
                                                if(cred) {
                                                    bodyHtml += '<li>' + cred + '</li>';
                                                }
                                            });
                                            bodyHtml += '</ul></div>';
                                        }

                                    bodyHtml += '</div>';


                                Prompt({
                                    hdr: 'Copy Workflow',
                                    body: bodyHtml,
                                    action: function() {
                                        $('#prompt-modal').modal('hide');
                                        Wait('start');
                                        TemplateCopyService.copyWorkflow(template.id)
                                        .then(function(result) {
                                            Wait('stop');
                                            $state.go('templates.editWorkflowJobTemplate', {workflow_job_template_id: result.data.id}, {reload: true});
                                        }, function (data) {
                                            Wait('stop');
                                            ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                                msg: 'Call to copy template failed. POST returned status: ' + status });
                                        });
                                    },
                                    actionText: 'COPY',
                                    class: 'Modal-primaryButton'
                                });
                            }
                        }
                        else {
                            Alert('Error: Unable to copy workflow job template', 'You do not have permission to perform this action.');
                        }
                    }, function (data) {
                        Wait('stop');
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to copy template failed. GET returned status: ' + status });
                    });
                }
                else {
                    // Something went wrong - Let the user know that we're unable to copy because we don't know
                    // what type of job template this is
                    Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while copying.');
                }
            }
            else {
                Alert('Error: Unable to copy job', 'Template parameter is missing');
            }
        };
    }
];
