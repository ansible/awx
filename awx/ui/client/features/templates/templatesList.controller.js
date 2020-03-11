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
    GetBasePath,
    ngToast,
) {
    const vm = this || {};
    const [jobTemplate, workflowTemplate] = resolvedModels;

    const choices = workflowTemplate.options('actions.GET.type.choices')
        .concat(jobTemplate.options('actions.GET.type.choices'));

    let paginateQuerySet = {};

    vm.strings = strings;
    vm.templateTypes = mapChoices(choices);
    vm.activeId = parseInt($state.params.job_template_id || $state.params.workflow_job_template_id);
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
    vm.list = {
        iterator: 'template',
        name: 'templates'
    };
    vm.dataset = Dataset.data;
    vm.templates = Dataset.data.results;
    vm.defaultParams = $state.params.template_search;

    const toolbarSortDefault = {
        label: `${strings.get('sort.NAME_ASCENDING')}`,
        value: 'name'
    };

    vm.toolbarSortOptions = [
        toolbarSortDefault,
        { label: `${strings.get('sort.NAME_DESCENDING')}`, value: '-name' },
        { label: `${strings.get('sort.MODIFIED_ASCENDING')}`, value: 'modified' },
        { label: `${strings.get('sort.MODIFIED_DESCENDING')}`, value: '-modified' },
        { label: `${strings.get('sort.LAST_JOB_RUN_ASCENDING')}`, value: 'last_job_run' },
        { label: `${strings.get('sort.LAST_JOB_RUN_DESCENDING')}`, value: '-last_job_run' },
        { label: `${strings.get('sort.INVENTORY_ASCENDING')}`, value: 'job_template__inventory__id' },
        { label: `${strings.get('sort.INVENTORY_DESCENDING')}`, value: '-job_template__inventory__id' },
        { label: `${strings.get('sort.PROJECT_ASCENDING')}`, value: 'jobtemplate__project__id' },
        { label: `${strings.get('sort.PROJECT_DESCENDING')}`, value: '-jobtemplate__project__id' },
    ];

    vm.toolbarSortValue = toolbarSortDefault;

    $scope.$on('updateDataset', (event, dataset, queryset) => {
        paginateQuerySet = queryset;
    });

    vm.onToolbarSort = (sort) => {
        vm.toolbarSortValue = sort;

        const queryParams = Object.assign(
            {},
            $state.params.template_search,
            paginateQuerySet,
            { order_by: sort.value }
        );

        // Update params
        $state.go('.', {
            template_search: queryParams
        }, { notify: false, location: 'replace' });
    };

    $scope.$watch('vm.dataset.count', () => {
        $scope.$emit('updateCount', vm.dataset.count, 'templates');
    });

    $scope.$watch('$state.params', function(newValue, oldValue) {
        const job_template_id = _.get($state.params, 'job_template_id');
        const workflow_job_template_id = _.get($state.params, 'workflow_job_template_id');

        if((job_template_id || workflow_job_template_id)) {
            vm.activeId = parseInt($state.params.job_template_id || $state.params.workflow_job_template_id);
        } else {
            vm.activeId = "";
        }
        setToolbarSort();
    }, true);

    $scope.$on(`ws-jobs`, (e, msg) => {
        if (msg.unified_job_template_id && vm.templates) {
            const template = vm.templates.find((t) => t.id === msg.unified_job_template_id);
            if (template) {
                if (msg.status === 'pending') {
                    // This is a new job - add it to the front of the
                    // recent_jobs array
                    if (template.summary_fields.recent_jobs.length === 10) {
                        template.summary_fields.recent_jobs.pop();
                    }

                    template.summary_fields.recent_jobs.unshift({
                        id: msg.unified_job_id,
                        status: msg.status,
                        type: msg.type
                    });
                } else {
                    // This is an update to an existing job.  Check to see
                    // if we have it in our array of recent_jobs
                    for (let i=0; i<template.summary_fields.recent_jobs.length; i++) {
                        const recentJob = template.summary_fields.recent_jobs[i];
                        if (recentJob.id === msg.unified_job_id) {
                            recentJob.status = msg.status;
                            if (msg.finished) {
                                recentJob.finished = msg.finished;
                                template.last_job_run = msg.finished;
                            }
                            break;
                        }
                    };
                }
            }
        }
    });

    vm.isInvalid = (template) => {
        if(isJobTemplate(template)) {
            return template.project === null || (template.inventory === null && template.ask_inventory_on_launch === false);
        } else {
            return false;
        }
    };

    vm.isPortalMode = $state.includes('portalMode');

    vm.openWorkflowVisualizer = template => {
        const name = 'templates.editWorkflowJobTemplate.workflowMaker';
        const params = { workflow_job_template_id: template.id };
        const options = { reload: true };

        $state.go(name, params, options);
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

    vm.buildCredentialTags = (credentials) => {
        return credentials.map(credential => {
            const icon = `${credential.kind}`;
            const link = `/#/credentials/${credential.id}`;
            const tooltip = strings.get('tooltips.VIEW_THE_CREDENTIAL');
            const value = $filter('sanitize')(credential.name);

            return { icon, link, tooltip, value };
        });
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

    vm.getType = template => {
        if(isJobTemplate(template)) {
            return strings.get('list.ADD_DD_JT_LABEL');
        } else {
            return strings.get('list.ADD_DD_WF_LABEL');;
        }
    };

    function setToolbarSort () {
        const orderByValue = _.get($state.params, 'template_search.order_by');
        const sortValue = _.find(vm.toolbarSortOptions, (option) => option.value === orderByValue);
        if (sortValue) {
            vm.toolbarSortValue = sortValue;
        } else {
            vm.toolbarSortValue = toolbarSortDefault;
        }
    }

    function refreshTemplates() {
        Wait('start');
        let path = GetBasePath('unified_job_templates');
        qs.search(path, $state.params.template_search, { 'X-WS-Session-Quiet': true })
        .then(function(searchResponse) {
            vm.dataset = searchResponse.data;
            vm.templates = vm.dataset.results;
        })
        .finally(() => Wait('stop'));
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
            .then((copiedJT) => {
                ngToast.success({
                    content: `
                        <div class="Toast-wrapper">
                            <div class="Toast-icon">
                                <i class="fa fa-check-circle Toast-successIcon"></i>
                            </div>
                            <div>
                                ${strings.get('SUCCESSFUL_CREATION', copiedJT.name)}
                            </div>
                        </div>`,
                    dismissButton: false,
                    dismissOnTimeout: true
                });
                refreshTemplates();
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
                        .then((copiedWFJT) => {
                            ngToast.success({
                                content: `
                                    <div class="Toast-wrapper">
                                        <div class="Toast-icon">
                                            <i class="fa fa-check-circle Toast-successIcon"></i>
                                        </div>
                                        <div>
                                            ${strings.get('SUCCESSFUL_CREATION', copiedWFJT.name)}
                                        </div>
                                    </div>`,
                                dismissButton: false,
                                dismissOnTimeout: true
                            });
                            refreshTemplates();
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
                        hdr: strings.get('listActions.COPY', template.name),
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

        if (vm.templates.length === 1 && page && page !== '1') {
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

    vm.isCollapsed = true;

    vm.onCollapse = () => {
        vm.isCollapsed = true;
    };

    vm.onExpand = () => {
        vm.isCollapsed = false;
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
    'resolvedModels',
    'TemplatesStrings',
    'Wait',
    'QuerySet',
    'GetBasePath',
    'ngToast'
];

export default ListTemplatesController;
