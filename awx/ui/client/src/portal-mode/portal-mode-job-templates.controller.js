/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function PortalModeJobTemplatesController($scope, PortalJobTemplateList, Dataset, $state, PromptService, JobTemplate, ProcessErrors) {

    var list = PortalJobTemplateList;
    // search init
    $scope.list = list;
    $scope[`${list.iterator}_dataset`] = Dataset.data;
    $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

    const jobTemplate = new JobTemplate();

    $scope.submitJob = function(id) {
        const selectedJobTemplate = jobTemplate.create();
        const preLaunchPromises = [
            selectedJobTemplate.getLaunch(id),
            selectedJobTemplate.optionsLaunch(id),
        ];

        Promise.all(preLaunchPromises)
            .then(([launchData, launchOptions]) => {
                if (selectedJobTemplate.canLaunchWithoutPrompt()) {
                    return selectedJobTemplate
                        .postLaunch({ id: id })
                        .then(({ data }) => {
                            $state.go('jobResult', { id: data.job }, { reload: true });
                        });
                }

                const promptData = {
                    launchConf: launchData.data,
                    launchOptions: launchOptions.data,
                    template: id,
                    templateType: 'job_template',
                    prompts: PromptService.processPromptValues({
                        launchConf: launchData.data,
                        launchOptions: launchOptions.data
                    }),
                    triggerModalOpen: true,
                };

                if (launchData.data.survey_enabled) {
                   selectedJobTemplate.getSurveyQuestions(id)
                        .then(({ data }) => {
                            const processed = PromptService.processSurveyQuestions({ surveyQuestions: data.spec });
                            promptData.surveyQuestions = processed.surveyQuestions;
                            $scope.promptData = promptData;
                        });
                } else {
                    $scope.promptData = promptData;
                }
            });
    };

    $scope.launchJob = () => {
        const jobLaunchData = PromptService.bundlePromptDataForLaunch($scope.promptData);

        // If the extra_vars dict is empty, we don't want to include it if we didn't prompt for anything.
        if(_.isEmpty(jobLaunchData.extra_vars) && !($scope.promptData.launchConf.ask_variables_on_launch && $scope.promptData.launchConf.survey_enabled && $scope.promptData.surveyQuestions.length > 0)){
            delete jobLaunchData.extra_vars;
        }

        jobTemplate.create().postLaunch({
            id: $scope.promptData.template,
            launchData: jobLaunchData
        })
        .then((launchRes) => {
            $state.go('jobResult', { id: launchRes.data.job }, { reload: true });
        })
        .catch(({data, status}) => {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to launch job template: ' + status });
        });

    };

}

PortalModeJobTemplatesController.$inject = ['$scope','PortalJobTemplateList', 'job_templatesDataset', '$state', 'PromptService', 'JobTemplateModel', 'ProcessErrors'];
