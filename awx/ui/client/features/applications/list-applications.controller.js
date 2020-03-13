/** ***********************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 ************************************************ */
function ListApplicationsController (
    $filter,
    $scope,
    $state,
    Dataset,
    ProcessErrors,
    Prompt,
    resolvedModels,
    strings,
    Wait
) {
    const vm = this || {};
    const application = resolvedModels;
    let paginateQuerySet = {};

    vm.strings = strings;
    vm.activeId = $state.params.application_id;

    $scope.canAdd = application.options('actions.POST');

    // smart-search
    const name = 'applications';
    const iterator = 'application';
    const key = 'application_dataset';

    $scope.list = { iterator, name, basePath: 'applications' };
    $scope.collection = { iterator };
    $scope[key] = Dataset.data;
    vm.applicationsCount = Dataset.data.count;
    $scope[name] = Dataset.data.results;

    $scope.$on('updateDataset', (e, dataset, queryset) => {
        $scope[key] = dataset;
        $scope[name] = dataset.results;
        vm.applicationsCount = dataset.count;
        // Remove paginateQuerySet once the page and page_size params
        // are represented in the url.
        paginateQuerySet = queryset;
    });

    const toolbarSortDefault = {
        label: `${strings.get('sort.NAME_ASCENDING')}`,
        value: 'name'
    };

    vm.toolbarSortOptions = [
        toolbarSortDefault,
        { label: `${strings.get('sort.NAME_DESCENDING')}`, value: '-name' },
        { label: `${strings.get('sort.CREATED_ASCENDING')}`, value: 'created' },
        { label: `${strings.get('sort.CREATED_DESCENDING')}`, value: '-created' }
    ];

    vm.toolbarSortValue = toolbarSortDefault;

    function setToolbarSort () {
        const orderByValue = _.get($state.params, 'application_search.order_by');
        const sortValue = _.find(vm.toolbarSortOptions, (option) => option.value === orderByValue);
        if (sortValue) {
            vm.toolbarSortValue = sortValue;
        } else {
            vm.toolbarSortValue = toolbarSortDefault;
        }
    }

    $scope.$watch('$state.params', () => {
        setToolbarSort();
    }, true);

    vm.onToolbarSort = (sort) => {
        vm.toolbarSortValue = sort;

        const queryParams = Object.assign(
            {},
            $state.params.application_search,
            paginateQuerySet,
            { order_by: sort.value }
        );

        // Update URL with params
        $state.go('.', {
            application_search: queryParams
        }, { notify: false, location: 'replace' });
    };

    vm.getModified = app => {
        const modified = _.get(app, 'modified');

        if (!modified) {
            return undefined;
        }

        let html = $filter('longDate')(modified);

        const { username, id } = _.get(app, 'summary_fields.modified_by', {});

        if (username && id) {
            html += ` by <a href="/#/users/${id}">${$filter('sanitize')(username)}</a>`;
        }

        return html;
    };

    vm.deleteApplication = (app) => {
        const action = () => {
            $('#prompt-modal').modal('hide');
            Wait('start');
            application.request('delete', app.id)
                .then(() => {
                    let reloadListStateParams = null;

                    if ($scope.applications.length === 1 && $state.params.application_search &&
                    !_.isEmpty($state.params.application_search.page) &&
                    $state.params.application_search.page !== '1') {
                        const page = `${(parseInt(reloadListStateParams
                            .application_search.page, 10) - 1)}`;
                        reloadListStateParams = _.cloneDeep($state.params);
                        reloadListStateParams.application_search.page = page;
                    }

                    if (parseInt($state.params.application_id, 10) === app.id) {
                        $state.go('applications', reloadListStateParams, { reload: true });
                    } else {
                        $state.go('.', reloadListStateParams, { reload: true });
                    }
                })
                .catch(({ data, status }) => {
                    ProcessErrors($scope, data, status, null, {
                        hdr: strings.get('error.HEADER'),
                        msg: strings.get('error.CALL', { path: `${application.path}${app.id}`, status })
                    });
                })
                .finally(() => {
                    Wait('stop');
                });
        };

        const deleteModalBody = `<div class="Prompt-bodyQuery">${strings.get('deleteResource.CONFIRM', 'application')}</div>`;

        Prompt({
            hdr: strings.get('deleteResource.HEADER'),
            resourceName: $filter('sanitize')(app.name),
            body: deleteModalBody,
            action,
            actionText: strings.get('DELETE')
        });
    };
}

ListApplicationsController.$inject = [
    '$filter',
    '$scope',
    '$state',
    'Dataset',
    'ProcessErrors',
    'Prompt',
    'resolvedModels',
    'ApplicationsStrings',
    'Wait'
];

export default ListApplicationsController;
