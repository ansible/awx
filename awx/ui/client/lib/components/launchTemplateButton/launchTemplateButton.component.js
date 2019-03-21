import templateUrl from './launchTemplateButton.partial.html';

const atLaunchTemplate = {
    templateUrl,
    bindings: {
        template: '<',
        showTextButton: '<',
        disabled: '='
    },
    controller: ['JobTemplateModel', 'WorkflowJobTemplateModel', 'PromptService', '$state',
        'ComponentsStrings', 'ProcessErrors', '$scope', 'TemplatesStrings', 'Alert',
        atLaunchTemplateCtrl],
    controllerAs: 'vm'
};

function atLaunchTemplateCtrl (
    JobTemplate, WorkflowTemplate, PromptService, $state,
    componentsStrings, ProcessErrors, $scope, templatesStrings, Alert
) {
    const vm = this;
    const jobTemplate = new JobTemplate();
    const workflowTemplate = new WorkflowTemplate();
    vm.strings = componentsStrings;
    vm.launchTooltip = vm.strings.get('launchTemplate.DEFAULT');

    $scope.$watch('vm.disabled', (val) => {
        vm.launchTooltip = (val) ? vm.strings.get('launchTemplate.DISABLED') : vm.strings.get('launchTemplate.DEFAULT');
    });

    const createErrorHandler = (path, action) =>
        ({ data, status }) => {
            const hdr = templatesStrings.get('error.HEADER');
            const msg = templatesStrings.get('error.CALL', { path, action, status });
            ProcessErrors($scope, data, status, null, { hdr, msg });
        };

    vm.startLaunchTemplate = () => {
        if (!vm.disabled) {
            if (vm.template.type === 'job_template') {
                const selectedJobTemplate = jobTemplate.create();
                const preLaunchPromises = [
                    selectedJobTemplate.getLaunch(vm.template.id)
                        .catch(createErrorHandler(`/api/v2/job_templates/${vm.template.id}/launch`, 'GET')),
                    selectedJobTemplate.optionsLaunch(vm.template.id)
                        .catch(createErrorHandler(`/api/v2/job_templates/${vm.template.id}/launch`, 'OPTIONS'))
                ];

                Promise.all(preLaunchPromises)
                    .then(([launchData, launchOptions]) => {
                        // If we don't get both of these things then one of the
                        // promises was rejected
                        if (launchData && launchOptions) {
                            if (selectedJobTemplate.canLaunchWithoutPrompt()) {
                                selectedJobTemplate
                                    .postLaunch({ id: vm.template.id })
                                    .then(({ data }) => {
                                        /* Slice Jobs: Redirect to WF Details page if returned
                                        job type is a WF job */
                                        if (data.type === 'workflow_job' && data.workflow_job !== null) {
                                            $state.go('workflowResults', { id: data.workflow_job }, { reload: true });
                                        } else {
                                            $state.go('output', { id: data.job, type: 'playbook' }, { reload: true });
                                        }
                                    })
                                    .catch(createErrorHandler(`/api/v2/job_templates/${vm.template.id}/launch`, 'POST'));
                            } else {
                                const promptData = {
                                    launchConf: launchData.data,
                                    launchOptions: launchOptions.data,
                                    template: vm.template.id,
                                    templateName: vm.template.name,
                                    templateType: vm.template.type,
                                    prompts: PromptService.processPromptValues({
                                        launchConf: launchData.data,
                                        launchOptions: launchOptions.data
                                    }),
                                    triggerModalOpen: true
                                };

                                if (launchData.data.survey_enabled) {
                                    selectedJobTemplate.getSurveyQuestions(vm.template.id)
                                        .then(({ data }) => {
                                            const processed = PromptService.processSurveyQuestions({
                                                surveyQuestions: data.spec
                                            });
                                            promptData.surveyQuestions = processed.surveyQuestions;
                                            vm.promptData = promptData;
                                        })
                                        .catch(createErrorHandler(`/api/v2/job_templates/${vm.template.id}/survey_spec`, 'GET'));
                                } else {
                                    vm.promptData = promptData;
                                }
                            }
                        }
                    });
            } else if (vm.template.type === 'workflow_job_template') {
                const selectedWorkflowJobTemplate = workflowTemplate.create();
                const preLaunchPromises = [
                    selectedWorkflowJobTemplate.request('get', vm.template.id)
                        .catch(createErrorHandler(`/api/v2/workflow_job_templates/${vm.template.id}`, 'GET')),
                    selectedWorkflowJobTemplate.getLaunch(vm.template.id)
                        .catch(createErrorHandler(`/api/v2/workflow_job_templates/${vm.template.id}/launch`, 'GET')),
                    selectedWorkflowJobTemplate.optionsLaunch(vm.template.id)
                        .catch(createErrorHandler(`/api/v2/workflow_job_templates/${vm.template.id}/launch`, 'OPTIONS')),
                ];

                Promise.all(preLaunchPromises)
                    .then(([wfjtData, launchData, launchOptions]) => {
                        // If we don't get all of these things then one of the
                        // promises was rejected
                        if (wfjtData && launchData && launchOptions) {
                            if (selectedWorkflowJobTemplate.canLaunchWithoutPrompt()) {
                                selectedWorkflowJobTemplate
                                    .postLaunch({ id: vm.template.id })
                                    .then(({ data }) => {
                                        $state.go('workflowResults', { id: data.workflow_job }, { reload: true });
                                    })
                                    .catch(createErrorHandler(`/api/v2/workflow_job_templates/${vm.template.id}/launch`, 'POST'));
                            } else {
                                launchData.data.defaults.extra_vars = wfjtData.data.extra_vars;

                                const promptData = {
                                    launchConf: selectedWorkflowJobTemplate.getLaunchConf(),
                                    launchOptions: launchOptions.data,
                                    template: vm.template.id,
                                    templateName: vm.template.name,
                                    templateType: vm.template.type,
                                    prompts: PromptService.processPromptValues({
                                        launchConf: selectedWorkflowJobTemplate.getLaunchConf(),
                                        launchOptions: launchOptions.data
                                    }),
                                    triggerModalOpen: true,
                                };

                                if (launchData.data.survey_enabled) {
                                    selectedWorkflowJobTemplate.getSurveyQuestions(vm.template.id)
                                        .then(({ data }) => {
                                            const processed = PromptService.processSurveyQuestions({
                                                surveyQuestions: data.spec
                                            });
                                            promptData.surveyQuestions = processed.surveyQuestions;
                                            vm.promptData = promptData;
                                        })
                                        .catch(createErrorHandler(`/api/v2/workflow_job_templates/${vm.template.id}/survey_spec`, 'GET'));
                                } else {
                                    vm.promptData = promptData;
                                }
                            }
                        }
                    });
            } else {
                Alert(templatesStrings.get('error.UNKNOWN'), templatesStrings.get('alert.UNKNOWN_LAUNCH'));
            }
        }
    };

    vm.launchTemplateWithPrompts = () => {
        const jobLaunchData = PromptService.bundlePromptDataForLaunch(vm.promptData);

        // If the extra_vars dict is empty, we don't want to include it
        // if we didn't prompt for anything.
        if (
            _.isEmpty(jobLaunchData.extra_vars) &&
            !(
                vm.promptData.launchConf.ask_variables_on_launch &&
                vm.promptData.launchConf.survey_enabled &&
                vm.promptData.surveyQuestions.length > 0
            )
        ) {
            delete jobLaunchData.extra_vars;
        }

        if (vm.promptData.templateType === 'job_template') {
            jobTemplate.create().postLaunch({
                id: vm.promptData.template,
                launchData: jobLaunchData
            }).then((launchRes) => {
                /* Slice Jobs: Redirect to WF Details page if returned
                job type is a WF job */
                if (launchRes.data.type === 'workflow_job' && launchRes.data.workflow_job !== null) {
                    $state.go('workflowResults', { id: launchRes.data.workflow_job }, { reload: true });
                } else {
                    $state.go('output', { id: launchRes.data.job, type: 'playbook' }, { reload: true });
                }
            }).catch(createErrorHandler(`/api/v2/job_templates/${vm.template.id}/launch`, 'POST'));
        } else if (vm.promptData.templateType === 'workflow_job_template') {
            workflowTemplate.create().postLaunch({
                id: vm.promptData.template,
                launchData: jobLaunchData
            }).then((launchRes) => {
                $state.go('workflowResults', { id: launchRes.data.workflow_job }, { reload: true });
            }).catch(createErrorHandler(`/api/v2/workflow_job_templates/${vm.template.id}/launch`, 'POST'));
        }
    };
}

export default atLaunchTemplate;
