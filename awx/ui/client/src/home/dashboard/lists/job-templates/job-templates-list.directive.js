/* jshint unused: vars */
export default
    [   'templateUrl',
        '$state',
        'Alert',
        'JobTemplateModel',
        'WorkflowJobTemplateModel',
        'PromptService',
        'ProcessErrors',
        function JobTemplatesList(templateUrl, $state, Alert, JobTemplate, WorkflowJobTemplate, PromptService, ProcessErrors) {
            return {
                restrict: 'E',
                link: link,
                scope: {
                    data: '='
                },
                templateUrl: templateUrl('home/dashboard/lists/job-templates/job-templates-list')
            };

            function link(scope, element, attr) {
                const jobTemplate = new JobTemplate();
                const workflowTemplate = new WorkflowJobTemplate();

                scope.$watch("data", function(data) {
                    if (data) {
                        if (data.length > 0) {
                            createList(data);
                            scope.noJobTemplates = false;
                        } else {
                            scope.noJobTemplates = true;
                        }
                    }
                });

                function createList(list) {
                    // smartStatus?, launchUrl, editUrl, name
                    scope.templates = _.map(list, function(template){ return {
                        recent_jobs: template.summary_fields.recent_jobs,
                        name: template.name,
                        id: template.id,
                        type: template.type
                    }; });
                }

                scope.isSuccessful = function (status) {
                    return (status === "successful");
                };

                scope.launchTemplate = function(template){
                    if(template) {
                        if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                            const selectedJobTemplate = jobTemplate.create();
                            const preLaunchPromises = [
                                selectedJobTemplate.getLaunch(template.id),
                                selectedJobTemplate.optionsLaunch(template.id),
                            ];

                            Promise.all(preLaunchPromises)
                                .then(([launchData, launchOptions]) => {
                                    if (selectedJobTemplate.canLaunchWithoutPrompt()) {
                                        return selectedJobTemplate
                                            .postLaunch({ id: template.id })
                                            .then(({ data }) => {
                                                $state.go('jobResult', { id: data.job }, { reload: true });
                                            });
                                    }

                                    const promptData = {
                                        launchConf: launchData.data,
                                        launchOptions: launchOptions.data,
                                        template: template.id,
                                        templateType: template.type,
                                        prompts: PromptService.processPromptValues({
                                            launchConf: launchData.data,
                                            launchOptions: launchOptions.data
                                        }),
                                        triggerModalOpen: true,
                                    };

                                    if (launchData.data.survey_enabled) {
                                       selectedJobTemplate.getSurveyQuestions(template.id)
                                            .then(({ data }) => {
                                                const processed = PromptService.processSurveyQuestions({ surveyQuestions: data.spec });
                                                promptData.surveyQuestions = processed.surveyQuestions;
                                                scope.promptData = promptData;
                                            });
                                    } else {
                                        scope.promptData = promptData;
                                    }
                                });
                        }
                        else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                            const selectedWorkflowJobTemplate = workflowTemplate.create();
                            const preLaunchPromises = [
                                selectedWorkflowJobTemplate.getLaunch(template.id),
                                selectedWorkflowJobTemplate.optionsLaunch(template.id),
                            ];

                            Promise.all(preLaunchPromises)
                                .then(([launchData, launchOptions]) => {
                                    if (selectedWorkflowJobTemplate.canLaunchWithoutPrompt()) {
                                        return selectedWorkflowJobTemplate
                                            .postLaunch({ id: template.id })
                                            .then(({ data }) => {
                                                $state.go('workflowResults', { id: data.workflow_job }, { reload: true });
                                            });
                                    }

                                    const promptData = {
                                        launchConf: launchData.data,
                                        launchOptions: launchOptions.data,
                                        template: template.id,
                                        templateType: template.type,
                                        prompts: PromptService.processPromptValues({
                                            launchConf: launchData.data,
                                            launchOptions: launchOptions.data
                                        }),
                                        triggerModalOpen: true,
                                    };

                                    if (launchData.data.survey_enabled) {
                                       selectedWorkflowJobTemplate.getSurveyQuestions(template.id)
                                            .then(({ data }) => {
                                                const processed = PromptService.processSurveyQuestions({ surveyQuestions: data.spec });
                                                promptData.surveyQuestions = processed.surveyQuestions;
                                                scope.promptData = promptData;
                                            });
                                    } else {
                                        scope.promptData = promptData;
                                    }
                                });
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

                scope.launchJob = () => {
                    const jobLaunchData = PromptService.bundlePromptDataForLaunch(scope.promptData);

                    // If the extra_vars dict is empty, we don't want to include it if we didn't prompt for anything.
                    if(_.isEmpty(jobLaunchData.extra_vars) && !(scope.promptData.launchConf.ask_variables_on_launch && scope.promptData.launchConf.survey_enabled && scope.promptData.surveyQuestions.length > 0)){
                        delete jobLaunchData.extra_vars;
                    }

                    if(scope.promptData.templateType === 'job_template') {
                        jobTemplate.create().postLaunch({
                            id: scope.promptData.template,
                            launchData: jobLaunchData
                        })
                        .then((launchRes) => {
                            $state.go('jobResult', { id: launchRes.data.job }, { reload: true });
                        })
                        .catch(({data, status}) => {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Failed to launch job template: ' + status });
                        });
                    } else if(scope.promptData.templateType === 'workflow_job_template') {
                        workflowTemplate.create().postLaunch({
                            id: scope.promptData.template,
                            launchData: jobLaunchData
                        })
                        .then((launchRes) => {
                            $state.go('workflowResults', { id: launchRes.data.workflow_job }, { reload: true });
                        })
                        .catch(({data, status}) => {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Failed to launch workflow job template: ' + status });
                        });
                    }

                };

                scope.editTemplate = function (template) {
                    if(template) {
                        if(template.type && (template.type === 'Job Template' || template.type === 'job_template')) {
                            $state.go('templates.editJobTemplate', {job_template_id: template.id});
                        }
                        else if(template.type && (template.type === 'Workflow Job Template' || template.type === 'workflow_job_template')) {
                            $state.go('templates.editWorkflowJobTemplate', {workflow_job_template_id: template.id});
                        }
                    }
                };
            }
}];
