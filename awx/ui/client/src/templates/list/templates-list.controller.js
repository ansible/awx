/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$stateParams', 'Rest',
    'Alert','TemplateList', 'Prompt', 'ClearScope', 'ProcessErrors',
    'GetBasePath', 'InitiatePlaybookRun', 'Wait', '$state', '$filter',
    'Dataset', 'rbacUiControlService', 'TemplatesService','QuerySet',
    'GetChoices', 'TemplateCopyService',
    function(
        $scope, $rootScope, $location, $stateParams, Rest, Alert,
        TemplateList, Prompt, ClearScope, ProcessErrors, GetBasePath,
        InitiatePlaybookRun, Wait, $state, $filter, Dataset, rbacUiControlService, TemplatesService,
        qs, GetChoices, TemplateCopyService
    ) {
        ClearScope();

        var list = TemplateList;

        init();

        function init() {
            $scope.canAdd = false;

            rbacUiControlService.canAdd("job_templates")
                .then(function(canAddJobTemplate) {
                    $scope.canAddJobTemplate = canAddJobTemplate;
                });

            rbacUiControlService.canAdd("workflow_job_templates")
                .then(function(canAddWorkflowJobTemplate) {
                    $scope.canAddWorkflowJobTemplate = canAddWorkflowJobTemplate;
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
                    $scope.options.type.choices.every(function(choice) {
                        if (choice[0] === item.type) {
                            itm.type_label = choice[1];
                            return false;
                        }
                        return true;
                    });
                }
            });
        }


        $scope.$on(`ws-jobs`, function () {
            // @issue - this is no longer quite as ham-fisted but I'd like for someone else to take a peek
            // calling $state.reload(); here was problematic when launching a job because job launch also
            // attempts to transition the state and they were squashing each other.

            let path = GetBasePath(list.basePath) || GetBasePath(list.name);
            qs.search(path, $stateParams[`${list.iterator}_search`])
            .then(function(searchResponse) {
                $scope[`${list.iterator}_dataset`] = searchResponse.data;
                $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
            });
        });
        $scope.addJobTemplate = function() {
            $state.go('jobTemplates.add');
        };

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
                        hdr: 'Delete',
                        body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the template below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(template.name) + '</div>',
                        action: function() {

                            function handleSuccessfulDelete() {
                                // TODO: look at this
                                if (parseInt($state.params.id) === template.id) {
                                    $state.go("^", null, {reload: true});
                                } else {
                                    $state.go(".", null, {reload: true});
                                }
                                Wait('stop');
                            }

                            $('#prompt-modal').modal('hide');
                            Wait('start');
                            if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                                TemplatesService.deleteWorkflowJobTemplate(template.id)
                                .then(function () {
                                    handleSuccessfulDelete();
                                }, function (data) {
                                    Wait('stop');
                                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                        msg: 'Call to delete workflow job template failed. DELETE returned status: ' + status });
                                });
                            }
                            else if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                                TemplatesService.deleteJobTemplate(template.id)
                                .then(function () {
                                    handleSuccessfulDelete();
                                }, function (data) {
                                    Wait('stop');
                                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                        msg: 'Call to delete job template failed. DELETE returned status: ' + status });
                                });
                            }
                            else {
                                Wait('stop');
                                Alert('Error: Unable to determine template type', 'We were unable to determine this template\'s type while deleting.');
                            }
                        },
                        actionText: 'DELETE'
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
                            if(!result.data.warnings || _.isEmpty(result.data.warnings)) {
                                // Go ahead and copy the workflow - the user has full priveleges on all the resources
                                TemplateCopyService.copyWorkflow(template.id)
                                .then(function(result) {
                                    $state.go('templates.editWorkflowJobTemplate', {workflow_job_template_id: result.data.id}, {reload: true});
                                }, function (data) {
                                    Wait('stop');
                                    ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                                        msg: 'Call to copy template failed. POST returned status: ' + status });
                                });
                            }
                            else {

                                let bodyHtml = `
                                    <div class="Prompt-bodyQuery">
                                        You may not have access to all resources used by this workflow.  Resources that you don\'t have access to will not be copied and may result in an incomplete workflow.
                                    </div>
                                    <div class="Prompt-bodyTarget">`;

                                        // Go and grab all of the warning strings
                                        _.forOwn(result.data.warnings, function(warning) {
                                            if(warning) {
                                                _.forOwn(warning, function(warningString) {
                                                    bodyHtml += '<div>' + warningString + '</div>';
                                                });
                                            }
                                         } );

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
