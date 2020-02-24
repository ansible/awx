/** ***********************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 ************************************************ */
const mapChoices = choices => Object.assign(...choices.map(([k, v]) => ({ [k]: v })));

function ListJobsController (
    $scope,
    $state,
    Dataset,
    resolvedModels,
    strings,
    qs,
    Prompt,
    $filter,
    ProcessErrors,
    Wait,
    Rest,
    SearchBasePath,
    $timeout
) {
    const vm = this || {};
    const [unifiedJob] = resolvedModels;

    vm.strings = strings;

    let newJobs = [];

    // smart-search
    const name = 'jobs';
    const iterator = 'job';
    let paginateQuerySet = {};

    let launchModalOpen = false;
    let newJobsTimerRunning = false;

    vm.searchBasePath = SearchBasePath;

    vm.list = { iterator, name };
    vm.job_dataset = Dataset.data;
    vm.jobs = Dataset.data.results;

    $scope.$watch('$state.params', () => {
        setToolbarSort();
    }, true);

    const toolbarSortDefault = {
        label: `${strings.get('sort.FINISH_TIME_DESCENDING')}`,
        value: '-finished'
    };

    function setToolbarSort () {
        const orderByValue = _.get($state.params, 'job_search.order_by');
        const sortValue = _.find(vm.toolbarSortOptions, (option) => option.value === orderByValue);
        if (sortValue) {
            vm.toolbarSortValue = sortValue;
        } else {
            vm.toolbarSortValue = toolbarSortDefault;
        }
    }

    vm.toolbarSortOptions = [
        { label: `${strings.get('sort.NAME_ASCENDING')}`, value: 'name' },
        { label: `${strings.get('sort.NAME_DESCENDING')}`, value: '-name' },
        { label: `${strings.get('sort.FINISH_TIME_ASCENDING')}`, value: 'finished' },
        toolbarSortDefault,
        { label: `${strings.get('sort.START_TIME_ASCENDING')}`, value: 'started' },
        { label: `${strings.get('sort.START_TIME_DESCENDING')}`, value: '-started' },
        { label: `${strings.get('sort.LAUNCHED_BY_ASCENDING')}`, value: 'created_by__id' },
        { label: `${strings.get('sort.LAUNCHED_BY_DESCENDING')}`, value: '-created_by__id' },
        { label: `${strings.get('sort.PROJECT_ASCENDING')}`, value: 'unified_job_template__project__id' },
        { label: `${strings.get('sort.PROJECT_DESCENDING')}`, value: '-unified_job_template__project__id' }
    ];

    vm.toolbarSortValue = toolbarSortDefault;

    // Temporary hack to retrieve $scope.querySet from the paginate directive.
    // Remove this event listener once the page and page_size params
    // are represented in the url.
    $scope.$on('updateDataset', (event, dataset, queryset) => {
        paginateQuerySet = queryset;
        vm.jobs = dataset.results;
        vm.job_dataset = dataset;
    });

    vm.onToolbarSort = (sort) => {
        vm.toolbarSortValue = sort;

        const queryParams = Object.assign(
            {},
            $state.params.job_search,
            paginateQuerySet,
            { order_by: sort.value }
        );

        // Update URL with params
        $state.go('.', {
            job_search: queryParams
        }, { notify: false, location: 'replace' });
    };

    $scope.$watch('vm.job_dataset.count', () => {
        $scope.$emit('updateCount', vm.job_dataset.count, 'jobs');
    });

    const canAddRowsDynamically = () => {
        const orderByValue = _.get($state.params, 'job_search.order_by');
        const pageValue = _.get($state.params, 'job_search.page');
        const idInValue = _.get($state.params, 'job_search.id__in');

        return (!idInValue && (!pageValue || pageValue === '1')
            && (orderByValue === '-finished' || orderByValue === '-started'));
    };

    const updateJobRow = (msg) => {
        // Loop across the jobs currently shown and update the row
        // if it exists
        for (let i = 0; i < vm.jobs.length; i++) {
            if (vm.jobs[i].id === msg.unified_job_id) {
                // Update the job status.
                vm.jobs[i].status = msg.status;
                if (msg.finished) {
                    vm.jobs[i].finished = msg.finished;
                    const orderByValue = _.get($state.params, 'job_search.order_by');
                    if (orderByValue === '-finished') {
                        // Attempt to sort the rows in the list by their finish
                        // timestamp in descending order
                        vm.jobs.sort((a, b) =>
                            (!b.finished) - (!a.finished)
                            || new Date(b.finished) - new Date(a.finished));
                    }
                }
                break;
            }
        }
    };

    $scope.$on('ws-jobs', (e, msg) => {
        if (msg.status === 'pending' && canAddRowsDynamically()) {
            newJobs.push(msg.unified_job_id);
            if (!launchModalOpen && !newJobsTimerRunning) {
                fetchNewJobs();
            }
        } else if (!newJobs.includes(msg.unified_job_id)) {
            updateJobRow(msg);
        }
    });

    $scope.$on('launchModalOpen', (evt, isOpen) => {
        evt.stopPropagation();
        if (!isOpen && newJobs.length > 0) {
            fetchNewJobs();
        }
        launchModalOpen = isOpen;
    });

    if ($state.includes('instanceGroups')) {
        vm.emptyListReason = strings.get('list.NO_RUNNING');
    }

    vm.isPortalMode = $state.includes('portalMode');

    vm.jobTypes = mapChoices(unifiedJob.options('actions.GET.type.choices'));

    vm.buildCredentialTags = (credentials) =>
        credentials.map(credential => {
            const icon = `${credential.kind}`;
            const link = `/#/credentials/${credential.id}`;
            const value = $filter('sanitize')(credential.name);

            return { icon, link, value };
        });

    vm.getSecondaryTagLabel = (job) => {
        if (job.job_slice_number && job.job_slice_count && job.job_slice_count > 1) {
            return `${strings.get('list.SLICE_JOB')} ${job.job_slice_number}/${job.job_slice_count}`;
        }
        if (job.launch_type === 'webhook') {
            return strings.get('list.ROW_ITEM_LABEL_WEBHOOK');
        }
        return null;
    };

    vm.getTranslatedStatusString = (status) => {
        switch (status) {
            case 'new':
                return strings.get('list.NEW');
            case 'pending':
                return strings.get('list.PENDING');
            case 'waiting':
                return strings.get('list.WAITING');
            case 'running':
                return strings.get('list.RUNNING');
            case 'successful':
                return strings.get('list.SUCCESSFUL');
            case 'failed':
                return strings.get('list.FAILED');
            case 'error':
                return strings.get('list.ERROR');
            case 'canceled':
                return strings.get('list.CANCELED');
            default:
                return status;
        }
    };

    vm.getSref = ({ type, id }) => {
        let sref;

        switch (type) {
            case 'job':
                sref = `output({type: 'playbook', id: ${id}})`;
                break;
            case 'ad_hoc_command':
                sref = `output({type: 'command', id: ${id}})`;
                break;
            case 'system_job':
                sref = `output({type: 'system', id: ${id}})`;
                break;
            case 'project_update':
                sref = `output({type: 'project', id: ${id}})`;
                break;
            case 'inventory_update':
                sref = `output({type: 'inventory', id: ${id}})`;
                break;
            case 'workflow_job':
                sref = `workflowResults({id: ${id}})`;
                break;
            default:
                sref = '';
                break;
        }

        return sref;
    };

    vm.deleteJob = (job) => {
        const action = () => {
            $('#prompt-modal').modal('hide');
            Wait('start');
            Rest.setUrl(job.url);
            Rest.destroy()
                .then(() => {
                    let reloadListStateParams = null;

                    if (vm.jobs.length === 1 && $state.params.job_search &&
                        _.has($state, 'params.job_search.page') &&
                        $state.params.job_search.page !== '1') {
                        reloadListStateParams = _.cloneDeep($state.params);
                        reloadListStateParams.job_search.page =
                            (parseInt(reloadListStateParams.job_search.page, 10) - 1).toString();
                    }

                    $state.go('.', reloadListStateParams, { reload: true });
                })
                .catch(({ data, status }) => {
                    ProcessErrors($scope, data, status, null, {
                        hdr: strings.get('error.HEADER'),
                        msg: strings.get('error.CALL', { path: `${job.url}`, status })
                    });
                })
                .finally(() => {
                    Wait('stop');
                });
        };

        const deleteModalBody = `<div class="Prompt-bodyQuery">${strings.get('deleteResource.CONFIRM', 'job')}</div>`;

        Prompt({
            hdr: strings.get('deleteResource.HEADER'),
            resourceName: $filter('sanitize')(job.name),
            body: deleteModalBody,
            action,
            actionText: strings.get('DELETE'),
        });
    };

    vm.cancelJob = (job) => {
        const action = () => {
            $('#prompt-modal').modal('hide');
            Wait('start');
            Rest.setUrl(job.related.cancel);
            Rest.post()
                .then(() => {
                    let reloadListStateParams = null;

                    if (vm.jobs.length === 1 && $state.params.job_search &&
                        !_.isEmpty($state.params.job_search.page) &&
                        $state.params.job_search.page !== '1') {
                        const page = `${(parseInt(reloadListStateParams
                            .job_search.page, 10) - 1)}`;
                        reloadListStateParams = _.cloneDeep($state.params);
                        reloadListStateParams.job_search.page = page;
                    }

                    $state.go('.', reloadListStateParams, { reload: true });
                })
                .catch(({ data, status }) => {
                    ProcessErrors($scope, data, status, null, {
                        hdr: strings.get('error.HEADER'),
                        msg: strings.get('error.CALL', { path: `${job.url}`, status })
                    });
                })
                .finally(() => {
                    Wait('stop');
                });
        };

        const deleteModalBody = `<div class="Prompt-bodyQuery">${strings.get('cancelJob.SUBMIT_REQUEST')}</div>`;

        Prompt({
            hdr: strings.get('cancelJob.HEADER'),
            resourceName: $filter('sanitize')(job.name),
            body: deleteModalBody,
            action,
            actionText: strings.get('cancelJob.CANCEL_JOB'),
            cancelText: strings.get('cancelJob.RETURN')
        });
    };

    const fetchNewJobs = () => {
        newJobsTimerRunning = true;
        const newJobIdsFilter = newJobs.join(',');
        newJobs = [];
        const newJobsSearchParams = Object.assign({}, $state.params.job_search);
        newJobsSearchParams.count_disabled = 1;
        newJobsSearchParams.id__in = newJobIdsFilter;
        delete newJobsSearchParams.page_size;
        const stringifiedSearchParams = qs.encodeQueryset(newJobsSearchParams, false);
        Rest.setUrl(`${vm.searchBasePath}${stringifiedSearchParams}`);
        Rest.get()
            .then(({ data }) => {
                vm.job_dataset.count += data.results.length;
                const pageSize = parseInt($state.params.job_search.page_size, 10) || 20;
                const joinedJobs = data.results.concat(vm.jobs);
                vm.jobs = joinedJobs.length > pageSize
                    ? joinedJobs.slice(0, pageSize)
                    : joinedJobs;
                $timeout(() => {
                    if (canAddRowsDynamically()) {
                        if (newJobs.length > 0 && !launchModalOpen) {
                            fetchNewJobs();
                        } else {
                            newJobsTimerRunning = false;
                        }
                    } else {
                        // Bail out - one of [order_by, page, id__in] params has changed since we
                        // received these new job messages
                        newJobs = [];
                        newJobsTimerRunning = false;
                    }
                }, 5000);
            })
            .catch(({ data, status }) => {
                ProcessErrors($scope, data, status, null, {
                    hdr: strings.get('error.HEADER'),
                    msg: strings.get('error.CALL', {
                        path: `${vm.searchBasePath}${stringifiedSearchParams}`,
                        status
                    })
                });
            });
    };

    vm.isCollapsed = true;

    vm.onCollapse = () => {
        vm.isCollapsed = true;
    };

    vm.onExpand = () => {
        vm.isCollapsed = false;
    };
}

ListJobsController.$inject = [
    '$scope',
    '$state',
    'Dataset',
    'resolvedModels',
    'JobsStrings',
    'QuerySet',
    'Prompt',
    '$filter',
    'ProcessErrors',
    'Wait',
    'Rest',
    'SearchBasePath',
    '$timeout'
];

export default ListJobsController;
