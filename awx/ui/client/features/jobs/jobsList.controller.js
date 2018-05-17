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
    Rest
) {
    const vm = this || {};
    const [unifiedJob] = resolvedModels;

    vm.strings = strings;

    // smart-search
    const name = 'jobs';
    const iterator = 'job';
    const key = 'job_dataset';

    let launchModalOpen = false;
    let refreshAfterLaunchClose = false;

    $scope.list = { iterator, name };
    $scope.collection = { iterator, basePath: 'unified_jobs' };
    $scope[key] = Dataset.data;
    $scope[name] = Dataset.data.results;
    $scope.$on('updateDataset', (e, dataset) => {
        $scope[key] = dataset;
        $scope[name] = dataset.results;
    });
    $scope.$on('ws-jobs', () => {
        if (!launchModalOpen) {
            refreshJobs();
        } else {
            refreshAfterLaunchClose = true;
        }
    });

    $scope.$on('launchModalOpen', (evt, isOpen) => {
        evt.stopPropagation();
        if (!isOpen && refreshAfterLaunchClose) {
            refreshAfterLaunchClose = false;
            refreshJobs();
        }
        launchModalOpen = isOpen;
    });

    if ($state.includes('instanceGroups')) {
        vm.emptyListReason = strings.get('list.NO_RUNNING');
    }

    vm.jobTypes = mapChoices(unifiedJob.options('actions.GET.type.choices'));

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

                    if ($scope.jobs.length === 1 && $state.params.job_search &&
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

                    if ($scope.jobs.length === 1 && $state.params.job_search &&
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

    function refreshJobs () {
        qs.search(unifiedJob.path, $state.params.job_search)
            .then(({ data }) => {
                $scope.$emit('updateDataset', data);
            });
    }
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
    'Rest'
];

export default ListJobsController;
