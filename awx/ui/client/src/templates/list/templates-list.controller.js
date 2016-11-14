/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$location', '$stateParams', 'Rest', 'Alert',
    'TemplateList', 'Prompt', 'ClearScope', 'ProcessErrors', 'GetBasePath',
    'InitiatePlaybookRun', 'Wait', '$state', '$filter', 'Dataset', 'rbacUiControlService', 'TemplatesService',
    'QuerySet',
    function(
        $scope, $rootScope, $location, $stateParams, Rest, Alert,
        TemplateList, Prompt, ClearScope, ProcessErrors, GetBasePath,
        InitiatePlaybookRun, Wait, $state, $filter, Dataset, rbacUiControlService, TemplatesService,
        qs
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

            $rootScope.flashMessage = null;
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
                        body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the ' + (template.type === "Workflow Job Template" ? 'workflow ' : '') + 'job template below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(template.name) + '</div>',
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
    }
];
