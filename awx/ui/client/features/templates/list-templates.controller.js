/** ***********************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 ************************************************ */
const JOB_TEMPLATE_ALIASES = ['job_template', 'Job Template'];
const WORKFLOW_TEMPLATE_ALIASES = ['workflow_job_template', 'Workflow Job Template'];

const isJobTemplate = ({ type }) => JOB_TEMPLATE_ALIASES.indexOf(type) > -1;
const isWorkflowTemplate = ({ type }) => WORKFLOW_TEMPLATE_ALIASES.indexOf(type) > -1;
const mapChoices = choices => Object.assign(...choices.map(([k, v]) => ({[k]: v})));

function ListTemplatesController(
    $filter,
    $scope,
    $state,
    Alert,
    Dataset,
    ProcessErrors,
    Prompt,
    PromptService,
    resolvedModels,
    strings,
    Wait
) {
    const vm = this || {};
    const [jobTemplate, workflowTemplate] = resolvedModels;

    const choices = workflowTemplate.options('actions.GET.type.choices')
        .concat(jobTemplate.options('actions.GET.type.choices'));

    vm.strings = strings;
    vm.templateTypes = mapChoices(choices);
    vm.activeId = parseInt($state.params.job_template_id || $state.params.workflow_template_id);
    vm.invalidTooltip = {
        popover: {
            text: strings.get('error.INVALID'),
            on: 'mouseenter',
            icon: 'fa-exclamation',
            position: 'right',
            arrowHeight: 15
        }
    };

    $scope.canAddJobTemplate = jobTemplate.options('actions.POST');
    $scope.canAddWorkflowJobTemplate = workflowTemplate.options('actions.POST');
    $scope.canAdd = ($scope.canAddJobTemplate || $scope.canAddWorkflowJobTemplate);

    // smart-search
    const name = 'templates';
    const iterator = 'template';
    const key = 'template_dataset';

    $scope.list = { iterator, name };
    $scope.collection = { iterator, basePath: 'unified_job_templates' };
    $scope[key] = Dataset.data;
    $scope[name] = Dataset.data.results;
    $scope.$on('updateDataset', (e, dataset) => {
        $scope[key] = dataset;
        $scope[name] = dataset.results;
    });

    vm.isInvalid = (template) => {
        if(isJobTemplate(template)) {
            return template.project === null || (template.inventory === null && template.ask_inventory_on_launch === false);
        } else {
            return false;
        }
    };

    vm.runTemplate = template => {
        if (!template) {
            Alert(strings.get('error.LAUNCH'), strings.get('alert.MISSING_PARAMETER'));
            return;
        }

        if (isJobTemplate(template)) {
            runJobTemplate(template);
        } else if (isWorkflowTemplate(template)) {
            runWorkflowTemplate(template);
        } else {
            Alert(strings.get('error.UNKNOWN'), strings.get('alert.UNKNOWN_LAUNCH'));
        }
    };

    vm.scheduleTemplate = template => {
        if (!template) {
            Alert(strings.get('error.SCHEDULE'), strings.get('alert.MISSING_PARAMETER'));
            return;
        }

        if (isJobTemplate(template)) {
            $state.go('jobTemplateSchedules', { id: template.id });
        } else if (isWorkflowTemplate(template)) {
            $state.go('workflowJobTemplateSchedules', { id: template.id });
        } else {
            Alert(strings.get('error.UNKNOWN'), strings.get('alert.UNKNOWN_SCHEDULE'));
        }
    };

    vm.deleteTemplate = template => {
        if (!template) {
            Alert(strings.get('error.DELETE'), strings.get('alert.MISSING_PARAMETER'));
            return;
        }

        if (isWorkflowTemplate(template)) {
            displayWorkflowTemplateDeletePrompt(template);
        } else if (isJobTemplate(template)) {
             jobTemplate.getDependentResourceCounts(template.id)
                .then(counts => displayJobTemplateDeletePrompt(template, counts));
        } else {
            Alert(strings.get('error.UNKNOWN'), strings.get('alert.UNKNOWN_DELETE'));
        }
    };

    vm.copyTemplate = template => {
        if (!template) {
            Alert(strings.get('error.COPY'), strings.get('alert.MISSING_PARAMETER'));
            return;
        }

        if (isJobTemplate(template)) {
            copyJobTemplate(template);
        } else if (isWorkflowTemplate(template)) {
            copyWorkflowTemplate(template);
        } else {
            Alert(strings.get('error.UNKNOWN'), strings.get('alert.UNKNOWN_COPY'));
        }
    };

    vm.getModified = template => {
        const modified = _.get(template, 'modified');

        if (!modified) {
            return undefined;
        }

        let html = $filter('longDate')(modified);

        const { username, id } = _.get(template, 'summary_fields.modified_by', {});

        if (username && id) {
            html += ` by <a href="/#/users/${id}">${$filter('sanitize')(username)}</a>`;
        }

        return html;
    };

    vm.getLastRan = template => {
        const lastJobRun = _.get(template, 'last_job_run');

        if (!lastJobRun) {
            return undefined;
        }

        let html = $filter('longDate')(lastJobRun);

        // TODO: uncomment and update when last job run user is returned by api
        // const { username, id } = _.get(template, 'summary_fields.last_job_run_by', {});

        // if (username && id) {
        //    html += ` by <a href="/#/users/${id}">${$filter('sanitize')(username)}</a>`;
        //}

        return html;
    };

    function createErrorHandler(path, action) {
        return ({ data, status }) => {
            const hdr = strings.get('error.HEADER');
            const msg = strings.get('error.CALL', { path, action, status });
            ProcessErrors($scope, data, status, null, { hdr, msg });
        };
    }

    function copyJobTemplate(template) {
        Wait('start');
        jobTemplate
            .create('get', template.id)
            .then(model => model.copy())
            .then(({ id }) => {
                const params = { job_template_id: id };
                $state.go('templates.editJobTemplate', params, { reload: true });
            })
            .catch(createErrorHandler('copy job template', 'POST'))
            .finally(() => Wait('stop'));
    }

    function copyWorkflowTemplate(template) {
        Wait('start');
        workflowTemplate
            .create('get', template.id)
            .then(model => model.extend('get', 'copy'))
            .then(model => {
                const action = () => {
                    Wait('start');
                    model.copy()
                        .then(({ id }) => {
                            const params = { workflow_job_template_id: id };
                            $state.go('templates.editWorkflowJobTemplate', params, { reload: true });
                        })
                        .catch(createErrorHandler('copy workflow', 'POST'))
                        .finally(() => Wait('stop'));
                };

                if (model.get('related.copy.can_copy_without_user_input')) {
                    action();
                } else if (model.get('related.copy.can_copy')) {
                    Prompt({
                        action,
                        actionText: strings.get('COPY'),
                        body: buildWorkflowCopyPromptHTML(model.get('related.copy')),
                        class: 'Modal-primaryButton',
                        hdr: strings.get('actions.COPY_WORKFLOW'),
                    });
                } else {
                    Alert(strings.get('error.COPY'), strings.get('alert.NO_PERMISSION'));
                }
            })
            .catch(createErrorHandler('copy workflow', 'GET'))
            .finally(() => Wait('stop'));
    }

    function handleSuccessfulDelete(template) {
        const { page } = _.get($state.params, 'template_search');
        let reloadListStateParams = null;

        if ($scope.templates.length === 1 && !_.isEmpty(page) && page !== '1') {
            reloadListStateParams = _.cloneDeep($state.params);
            const pageNumber = (parseInt(reloadListStateParams.template_search.page, 0) - 1);
            reloadListStateParams.template_search.page = pageNumber.toString();
        }

        if (parseInt($state.params.job_template_id, 0) === template.id) {
            $state.go('templates', reloadListStateParams, { reload: true });
        } else if (parseInt($state.params.workflow_job_template_id, 0) === template.id)  {
            $state.go('templates', reloadListStateParams, { reload: true });
        } else {
            $state.go('.', reloadListStateParams, { reload: true });
        }
    }

    function displayJobTemplateDeletePrompt(template, counts) {
        Prompt({
            action() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                jobTemplate
                    .request('delete', template.id)
                    .then(() => handleSuccessfulDelete(template))
                    .catch(createErrorHandler('delete template', 'DELETE'))
                    .finally(() => Wait('stop'));
            },
            hdr: strings.get('DELETE'),
            resourceName: $filter('sanitize')(template.name),
            body: buildJobTemplateDeletePromptHTML(counts),
        });
    }

    function displayWorkflowTemplateDeletePrompt(template) {
        Prompt({
            action() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                workflowTemplate
                    .request('delete', template.id)
                    .then(() => handleSuccessfulDelete(template))
                    .catch(createErrorHandler('delete template', 'DELETE'))
                    .finally(() => Wait('stop'));
            },
            hdr: strings.get('DELETE'),
            resourceName: $filter('sanitize')(template.name),
            body: strings.get('deleteResource.CONFIRM', 'workflow template'),
        });
    }

    function buildJobTemplateDeletePromptHTML(counts) {
        const buildCount = count => `<span class="badge List-titleBadge">${count}</span>`;
        const buildLabel = label => `<span class="Prompt-warningResourceTitle">
            ${$filter('sanitize')(label)}</span>`;
        const buildCountLabel = ({ count, label }) => `<div>
            ${buildLabel(label)}${buildCount(count)}</div>`;

        const displayedCounts = counts.filter(({ count }) => count > 0);

        const html = `
            ${displayedCounts.length ? strings.get('deleteResource.USED_BY', 'job template') : ''}
            ${strings.get('deleteResource.CONFIRM', 'job template')}
            ${displayedCounts.map(buildCountLabel).join('')}
        `;

        return html;
    }

    function buildWorkflowCopyPromptHTML(data) {
        const pull = (data, param) => _.get(data, param, []).map($filter('sanitize'));

        const credentials = pull(data, 'credentials_unable_to_copy');
        const inventories = pull(data, 'inventories_unable_to_copy');
        const templates = pull(data, 'templates_unable_to_copy');

        const html = `
            <div class="Prompt-bodyQuery">
                ${strings.get('warnings.WORKFLOW_RESTRICTED_COPY')}
            </div>
            <div class="Prompt-bodyTarget">
                ${templates.length ? `<div>Unified Job Templates<ul>` : ''}
                ${templates.map(item => `<li>${item}</li>`).join('')}
                ${templates.length ? `</ul></div>` : ''}
            </div>
            <div class="Prompt-bodyTarget">
                ${credentials.length ? `<div>Credentials<ul>` : ''}
                ${credentials.map(item => `<li>${item}</li>`).join('')}
                ${credentials.length ? `</ul></div>` : ''}
            </div>
            <div class="Prompt-bodyTarget">
                ${inventories.length ? `<div>Inventories<ul>` : ''}
                ${inventories.map(item => `<li>${item}</li>`).join('')}
                ${inventories.length ? `</ul></div>` : ''}
            </div>
        `;

        return html;
    }

    function runJobTemplate(template) {
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
                            $scope.promptData = promptData;
                        });
                } else {
                    $scope.promptData = promptData;
                }
            });
    }

    function runWorkflowTemplate(template) {
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
                            $scope.promptData = promptData;
                        });
                } else {
                    $scope.promptData = promptData;
                }
            });
    }

    $scope.launchJob = () => {
        const jobLaunchData = PromptService.bundlePromptDataForLaunch($scope.promptData);

        // If the extra_vars dict is empty, we don't want to include it if we didn't prompt for anything.
        if(_.isEmpty(jobLaunchData.extra_vars) && !($scope.promptData.launchConf.ask_variables_on_launch && $scope.promptData.launchConf.survey_enabled && $scope.promptData.surveyQuestions.length > 0)){
            delete jobLaunchData.extra_vars;
        }

        if($scope.promptData.templateType === 'job_template') {
            jobTemplate.create().postLaunch({
                id: $scope.promptData.template,
                launchData: jobLaunchData
            })
            .then((launchRes) => {
                $state.go('jobResult', { id: launchRes.data.job }, { reload: true });
            })
            .catch(createErrorHandler('launch job template', 'POST'));
        } else if($scope.promptData.templateType === 'workflow_job_template') {
            workflowTemplate.create().postLaunch({
                id: $scope.promptData.template,
                launchData: jobLaunchData
            })
            .then((launchRes) => {
                $state.go('workflowResults', { id: launchRes.data.workflow_job }, { reload: true });
            })
            .catch(createErrorHandler('launch workflow job template', 'POST'));
        }

    };
}

ListTemplatesController.$inject = [
    '$filter',
    '$scope',
    '$state',
    'Alert',
    'Dataset',
    'ProcessErrors',
    'Prompt',
    'PromptService',
    'resolvedModels',
    'TemplatesStrings',
    'Wait'
];

export default ListTemplatesController;
