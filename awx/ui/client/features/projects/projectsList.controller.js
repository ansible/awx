/** ***********************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 ************************************************ */

const mapChoices = choices => Object.assign(...choices.map(([k, v]) => ({ [k]: v.toUpperCase() })));

function projectsListController (
    $filter, $scope, $rootScope, $state, $log, Dataset, Alert, Rest,
    ProcessErrors, resolvedModels, strings, Wait, ngToast,
    Prompt, GetBasePath, qs, ProjectUpdate,
) {
    const vm = this || {};
    const [ProjectModel] = resolvedModels;
    let paginateQuerySet = {};
    $scope.canAdd = ProjectModel.options('actions.POST');

    vm.strings = strings;
    vm.scm_choices = ProjectModel.options('actions.GET.scm_type.choices');
    vm.projectTypes = mapChoices(vm.scm_choices);

    // smart-search
    vm.list = {
        iterator: 'project',
        name: 'projects',
        basePath: 'projects',
    };
    vm.dataset = Dataset.data;
    vm.projects = Dataset.data.results;

    $scope.$watch('vm.dataset.count', () => {
        $scope.$emit('updateCount', vm.dataset.count, 'projects');
    });
    // build tooltips
    _.forEach(vm.projects, buildTooltips);
    $rootScope.flashMessage = null;

    // when a project is added/deleted, rebuild tooltips
    $scope.$watchCollection('vm.projects', () => {
        _.forEach(vm.projects, buildTooltips);
    });
    // show active item in the list
    $scope.$watch('$state.params', () => {
        const projectId = _.get($state.params, 'project_id');
        if ((projectId)) {
            vm.activeId = parseInt($state.params.project_id, 10);
        } else {
            vm.activeId = '';
        }
        setToolbarSort();
    }, true);

    function setToolbarSort () {
        const orderByValue = _.get($state.params, 'project_search.order_by');
        const sortValue = _.find(vm.toolbarSortOptions, (option) => option.value === orderByValue);
        if (sortValue) {
            vm.toolbarSortValue = sortValue;
        } else {
            vm.toolbarSortValue = toolbarSortDefault;
        }
    }

    const toolbarSortDefault = {
        label: `${strings.get('sort.NAME_ASCENDING')}`,
        value: 'name'
    };

    vm.toolbarSortOptions = [
        toolbarSortDefault,
        { label: `${strings.get('sort.NAME_DESCENDING')}`, value: '-name' },
        { label: `${strings.get('sort.MODIFIED_ASCENDING')}`, value: 'modified' },
        { label: `${strings.get('sort.MODIFIED_DESCENDING')}`, value: '-modified' },
        { label: `${strings.get('sort.LAST_USED_ASCENDING')}`, value: 'last_job_run' },
        { label: `${strings.get('sort.LAST_USED_DESCENDING')}`, value: '-last_job_run' },
        { label: `${strings.get('sort.ORGANIZATION_ASCENDING')}`, value: 'organization' },
        { label: `${strings.get('sort.ORGANIZATION_DESCENDING')}`, value: '-organization' }
    ];

    vm.toolbarSortValue = toolbarSortDefault;

    // Temporary hack to retrieve $scope.querySet from the paginate directive.
    // Remove this event listener once the page and page_size params
    // are represented in the url.
    $scope.$on('updateDataset', (event, dataset, queryset) => {
        vm.dataset = dataset;
        vm.projects = dataset.results;
        paginateQuerySet = queryset;
    });

    vm.onToolbarSort = (sort) => {
        vm.toolbarSortValue = sort;

        const queryParams = Object.assign(
            {},
            $state.params.project_search,
            paginateQuerySet,
            { order_by: sort.value }
        );

        // Update URL with params
        $state.go('.', {
            project_search: queryParams
        }, { notify: false, location: 'replace' });
    };

    $scope.$on('ws-jobs', (e, data) => {
        $log.debug(data);
        if (vm.projects) {
            // Assuming we have a list of projects available
            const project = vm.projects.find((p) => p.id === data.project_id);
            if (project) {
                // And we found the affected project
                $log.debug(`Received event for project: ${project.name}`);
                $log.debug(`Status changed to: ${data.status}`);
                project.status = data.status;
                buildTooltips(project);
            }
        }
    });

    if ($scope.removeGoTojobResults) {
        $scope.removeGoTojobResults();
    }

    $scope.removeGoTojobResults = $scope.$on('GoTojobResults', (e, data) => {
        if (data.summary_fields.current_update || data.summary_fields.last_update) {
            Wait('start');
            // Grab the id from summary_fields
            const updateJobid = (data.summary_fields.current_update) ?
                data.summary_fields.current_update.id : data.summary_fields.last_update.id;

            $state.go('output', { id: updateJobid, type: 'project' }, { reload: true });
        } else {
            Alert(vm.strings.get('alert.NO_UPDATE'), vm.strings.get('update.NO_UPDATE_INFO'), 'alert-info');
        }
    });

    if ($scope.removeCancelUpdate) {
        $scope.removeCancelUpdate();
    }

    $scope.removeCancelUpdate = $scope.$on('Cancel_Update', (e, url) => {
        // Cancel the project update process
        Rest.setUrl(url);
        Rest.post()
            .then(() => {
                Alert(vm.strings.get('alert.UPDATE_CANCEL'), vm.strings.get('update.CANCEL_UPDATE_REQUEST'), 'alert-info');
            })
            .catch(createErrorHandler(url, 'POST'));
    });

    if ($scope.removeCheckCancel) {
        $scope.removeCheckCancel();
    }

    $scope.removeCheckCancel = $scope.$on('Check_Cancel', (e, projectData) => {
        // Check that we 'can' cancel the update
        const url = projectData.related.cancel;
        Rest.setUrl(url);
        Rest.get()
            .then(({ data }) => {
                if (data.can_cancel) {
                    $scope.$emit('Cancel_Update', url);
                } else {
                    Alert(vm.strings.get('alert.CANCEL_NOT_ALLOWED'), vm.strings.get('update.NO_ACCESS_OR_COMPLETED_UPDATE'), 'alert-info', null, null, null, null, true);
                }
            })
            .catch(createErrorHandler(url, 'GET'));
    });

    vm.showSCMStatus = (id) => {
        // Refresh the project list
        const project = vm.projects.find((p) => p.id === id);

        if ((!project.scm_type) || project.scm_type === 'Manual') {
            Alert(vm.strings.get('alert.NO_SCM_CONFIG'), vm.strings.get('update.NO_PROJ_SCM_CONFIG'), 'alert-info');
        } else {
            // Refresh what we have in memory
            // to insure we're accessing the most recent status record
            Rest.setUrl(project.url);
            Rest.get()
                .then(({ data }) => {
                    $scope.$emit('GoTojobResults', data);
                })
                .catch(createErrorHandler(project.url, 'GET'));
        }
    };

    vm.getLastModified = project => {
        const modified = _.get(project, 'modified');

        if (!modified) {
            return undefined;
        }

        const html = $filter('longDate')(modified);

        // NEED api to add field  project.summary_fields.modified_by

        // const { username, id } = _.get(project, 'summary_fields.modified_by', {});

        // if (username && id) {
        //     html += ` by <a href="/#/users/${id}">${$filter('sanitize')(username)}</a>`;
        // }

        return html;
    };

    vm.getLastUsed = project => {
        const modified = _.get(project, 'last_job_run');

        if (!modified) {
            return undefined;
        }

        const html = $filter('longDate')(modified);

        // NEED api to add last_job user information such as launch_by

        // const { id } = _.get(project, 'summary_fields.last_job', {});
        // if (id) {
        //     html += ` by <a href="/#/jobs/project/${id}">
        // ${$filter('sanitize')('placehoder')}</a>`;
        // }
        return html;
    };

    vm.copyProject = project => {
        Wait('start');
        ProjectModel
            .create('get', project.id)
            .then(model => model.copy())
            .then((copiedProj) => {
                ngToast.success({
                    content: `
                        <div class="Toast-wrapper">
                            <div class="Toast-icon">
                                <i class="fa fa-check-circle Toast-successIcon"></i>
                            </div>
                            <div>
                                ${vm.strings.get('SUCCESSFUL_CREATION', copiedProj.name)}
                            </div>
                        </div>`,
                    dismissButton: false,
                    dismissOnTimeout: true
                });
                reloadList();
            })
            .catch(createErrorHandler('copy project', 'GET'))
            .finally(() => Wait('stop'));
    };

    vm.deleteProject = (id, name) => {
        const action = () => {
            $('#prompt-modal').modal('hide');
            Wait('start');
            ProjectModel
                .request('delete', id)
                .then(() => {
                    let reloadListStateParams = null;

                    if (vm.projects.length === 1
                        && $state.params.project_search
                        && _.has($state, 'params.project_search.page')
                        && $state.params.project_search.page !== '1') {
                        reloadListStateParams = _.cloneDeep($state.params);
                        reloadListStateParams.project_search.page =
                        (parseInt(reloadListStateParams.project_search.page, 10) - 1).toString();
                    }

                    if (parseInt($state.params.project_id, 10) === id) {
                        $state.go('^', reloadListStateParams, { reload: true });
                    } else {
                        $state.go('.', reloadListStateParams, { reload: true });
                    }
                })
                .catch(createErrorHandler(`${ProjectModel.path}${id}/`, 'DELETE'))
                .finally(() => {
                    Wait('stop');
                });
        };

        ProjectModel.getDependentResourceCounts(id)
            .then((counts) => {
                const invalidateRelatedLines = [];
                let deleteModalBody = `<div class="Prompt-bodyQuery">${vm.strings.get('deleteResource.CONFIRM', 'project')}</div>`;

                counts.forEach(countObj => {
                    if (countObj.count && countObj.count > 0) {
                        invalidateRelatedLines.push(`<div><span class="Prompt-warningResourceTitle">${countObj.label}</span><span class="badge List-titleBadge">${countObj.count}</span></div>`);
                    }
                });

                if (invalidateRelatedLines && invalidateRelatedLines.length > 0) {
                    deleteModalBody = `<div class="Prompt-bodyQuery">${vm.strings.get('deleteResource.USED_BY', 'project')} ${vm.strings.get('deleteResource.CONFIRM', 'project')}</div>`;
                    invalidateRelatedLines.forEach(invalidateRelatedLine => {
                        deleteModalBody += invalidateRelatedLine;
                    });
                }

                Prompt({
                    hdr: vm.strings.get('DELETE'),
                    resourceName: $filter('sanitize')(name),
                    body: deleteModalBody,
                    action,
                    actionText: vm.strings.get('DELETE'),
                });
            });
    };

    vm.cancelUpdate = (project) => {
        project.pending_cancellation = true;
        Rest.setUrl(GetBasePath('projects') + project.id);
        Rest.get()
            .then(({ data }) => {
                if (data.related.current_update) {
                    cancelSCMUpdate(data);
                } else {
                    Alert(vm.strings.get('update.UPDATE_NOT_FOUND'), vm.strings.get('update.NO_RUNNING_UPDATE') + $filter('sanitize')(project.name), 'alert-info', undefined, undefined, undefined, undefined, true);
                }
            })
            .catch(createErrorHandler('get project', 'GET'));
    };

    vm.SCMUpdate = (id, event) => {
        try {
            $(event.target).tooltip('hide');
        } catch (e) {
            // ignore
        }
        vm.projects.forEach((project) => {
            if (project.id === id) {
                if (project.scm_type === 'Manual' || (!project.scm_type)) {
                    // Do not respond. Button appears greyed out as if it is disabled.
                    // Not disabled though, because we need mouse over event
                    // to work. So user can click, but we just won't do anything.
                    // Alert('Missing SCM Setup', 'Before running an SCM update,
                    // edit the project and provide the SCM access information.', 'alert-info');
                } else if (project.status === 'updating' || project.status === 'running' || project.status === 'pending') {
                    // Alert('Update in Progress', 'The SCM update process is running.
                    // Use the Refresh button to monitor the status.', 'alert-info');
                } else {
                    ProjectUpdate({ scope: $scope, project_id: project.id });
                }
            }
        });
    };

    function buildTooltips (project) {
        project.statusIcon = getJobStatusIcon(project);
        project.statusTip = getStatusTooltip(project);
        project.scm_update_tooltip = vm.strings.get('update.GET_LATEST');
        project.scm_update_disabled = false;

        if (project.status === 'pending' || project.status === 'waiting') {
            project.scm_update_disabled = true;
        }

        if (project.status === 'failed' && project.summary_fields.last_update && project.summary_fields.last_update.status === 'canceled') {
            project.statusTip = vm.strings.get('status.UPDATE_CANCELED');
            project.scm_update_disabled = true;
        }

        if (project.status === 'running' || project.status === 'updating') {
            project.scm_update_tooltip = vm.strings.get('update.UPDATE_RUNNING');
            project.scm_update_disabled = true;
        }

        if (project.scm_type === 'manual') {
            project.statusIcon = 'none';
            project.statusTip = vm.strings.get('status.NOT_CONFIG');
            project.scm_update_tooltip = vm.strings.get('update.MANUAL_PROJECT_NO_UPDATE');
            project.scm_update_disabled = true;
        }
    }

    function cancelSCMUpdate (projectData) {
        Rest.setUrl(projectData.related.current_update);
        Rest.get()
            .then(({ data }) => {
                $scope.$emit('Check_Cancel', data);
            })
            .catch(createErrorHandler(projectData.related.current_update, 'GET'));
    }

    function reloadList () {
        Wait('start');
        const path = GetBasePath(vm.list.basePath) || GetBasePath(vm.list.name);
        qs.search(path, $state.params.project_search)
            .then((searchResponse) => {
                vm.dataset = searchResponse.data;
                vm.projects = vm.dataset.results;
            })
            .finally(() => Wait('stop'));
    }

    function createErrorHandler (path, action) {
        return ({ data, status }) => {
            const hdr = strings.get('error.HEADER');
            const msg = strings.get('error.CALL', { path, action, status });
            ProcessErrors($scope, data, status, null, { hdr, msg });
        };
    }

    function getJobStatusIcon (project) {
        let icon = 'none';
        switch (project.status) {
            case 'n/a':
            case 'ok':
            case 'never updated':
                icon = 'none';
                break;
            case 'pending':
            case 'waiting':
            case 'new':
                icon = 'none';
                break;
            case 'updating':
            case 'running':
                icon = 'running';
                break;
            case 'successful':
                icon = 'success';
                break;
            case 'failed':
            case 'missing':
            case 'canceled':
                icon = 'error';
                break;
            default:
                break;
        }
        return icon;
    }

    function getStatusTooltip (project) {
        let tooltip = '';
        switch (project.status) {
            case 'n/a':
            case 'ok':
            case 'never updated':
                tooltip = vm.strings.get('status.NEVER_UPDATE');
                break;
            case 'pending':
            case 'waiting':
            case 'new':
                tooltip = vm.strings.get('status.UPDATE_QUEUED');
                break;
            case 'updating':
            case 'running':
                tooltip = vm.strings.get('status.UPDATE_RUNNING');
                break;
            case 'successful':
                tooltip = vm.strings.get('status.UPDATE_SUCCESS');
                break;
            case 'failed':
                tooltip = vm.strings.get('status.UPDATE_FAILED');
                break;
            case 'missing':
                tooltip = vm.strings.get('status.UPDATE_MISSING');
                break;
            case 'canceled':
                tooltip = vm.strings.get('status.UPDATE_CANCELED');
                break;
            default:
                break;
        }
        return tooltip;
    }

    vm.isCollapsed = true;

    vm.onCollapse = () => {
        vm.isCollapsed = true;
    };

    vm.onExpand = () => {
        vm.isCollapsed = false;
    };
}

projectsListController.$inject = [
    '$filter',
    '$scope',
    '$rootScope',
    '$state',
    '$log',
    'Dataset',
    'Alert',
    'Rest',
    'ProcessErrors',
    'resolvedModels',
    'ProjectsStrings',
    'Wait',
    'ngToast',
    'Prompt',
    'GetBasePath',
    'QuerySet',
    'ProjectUpdate',
];

export default projectsListController;
