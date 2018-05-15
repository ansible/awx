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
    resolvedModels,
    strings,
    Wait,
    qs,
    GetBasePath
) {
    const vm = this || {};
    const [jobTemplate, workflowTemplate] = resolvedModels;

    const choices = workflowTemplate.options('actions.GET.type.choices')
        .concat(jobTemplate.options('actions.GET.type.choices'));

    let launchModalOpen = false;
    let refreshAfterLaunchClose = false;

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
    $scope.list = {
        iterator: 'template',
        name: 'templates'
    };
    $scope.collection = {
        iterator: 'template',
        basePath: 'unified_job_templates'
    };
    $scope.template_dataset = Dataset.data;
    $scope.templates = Dataset.data.results;
    $scope.$on('updateDataset', (e, dataset) => {
        $scope.template_dataset = dataset;
        $scope.templates = dataset.results;
    });

    $scope.$on(`ws-jobs`, () => {
        if (!launchModalOpen) {
            refreshTemplates();
        } else {
            refreshAfterLaunchClose = true;
        }
    });

    $scope.$on('launchModalOpen', (evt, isOpen) => {
        evt.stopPropagation();
        if (!isOpen && refreshAfterLaunchClose) {
            refreshAfterLaunchClose = false;
            refreshTemplates();
        }
        launchModalOpen = isOpen;
    });

    vm.isInvalid = (template) => {
        if(isJobTemplate(template)) {
            return template.project === null || (template.inventory === null && template.ask_inventory_on_launch === false);
        } else {
            return false;
        }
    };

    vm.scheduleTemplate = template => {
        if (!template) {
            Alert(strings.get('error.SCHEDULE'), strings.get('alert.MISSING_PARAMETER'));
            return;
        }

        if (isJobTemplate(template)) {
            $state.go('templates.editJobTemplate.schedules', { job_template_id: template.id });
        } else if (isWorkflowTemplate(template)) {
            $state.go('templates.editWorkflowJobTemplate.schedules', { workflow_job_template_id: template.id });
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

    function refreshTemplates() {
        let path = GetBasePath('unified_job_templates');
        qs.search(path, $state.params.template_search)
            .then(function(searchResponse) {
                $scope.template_dataset = searchResponse.data;
                $scope.templates = $scope.template_dataset.results;
            });
    }

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
                    $('#prompt-modal').modal('hide');
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
}

ListTemplatesController.$inject = [
    '$filter',
    '$scope',
    '$state',
    'Alert',
    'Dataset',
    'ProcessErrors',
    'Prompt',
    'resolvedModels',
    'TemplatesStrings',
    'Wait',
    'QuerySet',
    'GetBasePath'
];

export default ListTemplatesController;
