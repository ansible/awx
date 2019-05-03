/** ***********************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 ************************************************ */
function ListApplicationsUsersController (
    $filter,
    $scope,
    Dataset,
    strings,
    $state,
    GetBasePath
) {
    const vm = this || {};
    vm.strings = strings;

    // smart-search
    const name = 'users';
    const iterator = 'user';
    let paginateQuerySet = {};

    vm.user_dataset = Dataset.data;
    vm.users = Dataset.data.results;
    vm.list = { iterator, name, basePath: 'applications' };
    vm.basePath = `${GetBasePath('applications')}${$state.params.application_id}/tokens`;

    $scope.$on('updateDataset', (e, dataset, queryset) => {
        vm.user_dataset = dataset;
        vm.users = dataset.results;
        paginateQuerySet = queryset;
    });

    $scope.$watchCollection('$state.params', () => {
        setToolbarSort();
    });

    const toolbarSortDefault = {
        label: `${strings.get('sort.USERNAME_ASCENDING')}`,
        value: 'user__username'
    };

    vm.toolbarSortOptions = [
        toolbarSortDefault,
        { label: `${strings.get('sort.USERNAME_DESCENDING')}`, value: '-user__username' },
        { label: `${strings.get('sort.CREATED_ASCENDING')}`, value: 'created' },
        { label: `${strings.get('sort.CREATED_DESCENDING')}`, value: '-created' },
        { label: `${strings.get('sort.MODIFIED_ASCENDING')}`, value: 'modified' },
        { label: `${strings.get('sort.MODIFIED_DESCENDING')}`, value: '-modified' },
        { label: `${strings.get('sort.EXPIRES_ASCENDING')}`, value: 'expires' },
        { label: `${strings.get('sort.EXPIRES_DESCENDING')}`, value: '-expires' }
    ];

    function setToolbarSort () {
        const orderByValue = _.get($state.params, 'user_search.order_by');
        const sortValue = _.find(vm.toolbarSortOptions, (option) => option.value === orderByValue);
        if (sortValue) {
            vm.toolbarSortValue = sortValue;
        } else {
            vm.toolbarSortValue = toolbarSortDefault;
        }
    }

    vm.onToolbarSort = (sort) => {
        vm.toolbarSortValue = sort;
        const queryParams = Object.assign(
            {},
            $state.params.user_search,
            paginateQuerySet,
            { order_by: sort.value }
        );

        // Update URL with params
        $state.go('.', {
            user_search: queryParams
        }, { notify: false, location: 'replace' });
    };

    vm.getLastUsed = user => {
        const lastUsed = _.get(user, 'last_used');

        if (!lastUsed) {
            return undefined;
        }

        let html = $filter('longDate')(lastUsed);

        const { username, id } = _.get(user, 'summary_fields.last_used', {});

        if (username && id) {
            html += ` by <a href="/#/users/${id}">${$filter('sanitize')(username)}</a>`;
        }

        return html;
    };
}

ListApplicationsUsersController.$inject = [
    '$filter',
    '$scope',
    'Dataset',
    'ApplicationsStrings',
    '$state',
    'GetBasePath'
];

export default ListApplicationsUsersController;
