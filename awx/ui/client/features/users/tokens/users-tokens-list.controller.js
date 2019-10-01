/** ***********************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 ************************************************ */
function ListTokensController (
    $filter,
    $scope,
    $state,
    Dataset,
    strings,
    ProcessErrors,
    GetBasePath,
    Prompt,
    Wait,
    models
) {
    const vm = this || {};
    const { token } = models;

    vm.strings = strings;
    vm.activeId = $state.params.token_id;

    $scope.canAdd = true;

    // smart-search
    const name = 'tokens';
    const iterator = 'token';
    let paginateQuerySet = {};

    vm.token_dataset = Dataset.data;
    vm.tokens = Dataset.data.results;
    vm.list = { iterator, name, basePath: 'tokens' };
    vm.basePath = `${GetBasePath('users')}${$state.params.user_id}/tokens`;

    $scope.$on('updateDataset', (e, dataset, queryset) => {
        vm.token_dataset = dataset;
        vm.tokens = dataset.results;
        paginateQuerySet = queryset;
    });

    $scope.$watchCollection('$state.params', () => {
        setToolbarSort();
    });

    const toolbarSortDefault = {
        label: `${strings.get('sort.NAME_ASCENDING')}`,
        value: 'application__name'
    };

    vm.toolbarSortOptions = [
        toolbarSortDefault,
        { label: `${strings.get('sort.NAME_DESCENDING')}`, value: '-application__name' },
        { label: `${strings.get('sort.CREATED_ASCENDING')}`, value: 'created' },
        { label: `${strings.get('sort.CREATED_DESCENDING')}`, value: '-created' },
        { label: `${strings.get('sort.MODIFIED_ASCENDING')}`, value: 'modified' },
        { label: `${strings.get('sort.MODIFIED_DESCENDING')}`, value: '-modified' },
        { label: `${strings.get('sort.EXPIRES_ASCENDING')}`, value: 'expires' },
        { label: `${strings.get('sort.EXPIRES_DESCENDING')}`, value: '-expires' }
    ];

    function setToolbarSort () {
        const orderByValue = _.get($state.params, 'token_search.order_by');
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
            $state.params.token_search,
            paginateQuerySet,
            { order_by: sort.value }
        );

        // Update URL with params
        $state.go('.', {
            token_search: queryParams
        }, { notify: false, location: 'replace' });
    };

    vm.getScopeString = str => {
        if (str === 'Read') {
            return vm.strings.get('add.SCOPE_READ_LABEL');
        } else if (str === 'Write') {
            return vm.strings.get('add.SCOPE_WRITE_LABEL');
        }

        return undefined;
    };

    vm.getLastUsed = tokenToCheck => {
        const lastUsed = _.get(tokenToCheck, 'last_used');

        if (!lastUsed) {
            return undefined;
        }

        let html = $filter('longDate')(lastUsed);

        const { username, id } = _.get(tokenToCheck, 'summary_fields.last_used', {});

        if (username && id) {
            html += ` ${strings.get('add.LAST_USED_LABEL')} <a href="/#/users/${id}">${$filter('sanitize')(username)}</a>`;
        }

        return html;
    };

    vm.deleteToken = (tok) => {
        const action = () => {
            $('#prompt-modal').modal('hide');
            Wait('start');
            token.request('delete', tok.id)
                .then(() => {
                    let reloadListStateParams = null;

                    if ($scope.vm.tokens.length === 1 && $state.params.token_search &&
                    !_.isEmpty($state.params.token_search.page) &&
                    $state.params.token_search.page !== '1') {
                        const page = `${(parseInt(reloadListStateParams
                            .token_search.page, 10) - 1)}`;
                        reloadListStateParams = _.cloneDeep($state.params);
                        reloadListStateParams.token_search.page = page;
                    }

                    if (parseInt($state.params.token_id, 10) === tok.id) {
                        $state.go('^', reloadListStateParams, { reload: true });
                    } else {
                        $state.go('.', reloadListStateParams, { reload: true });
                    }
                }).catch(({ data, status }) => {
                    ProcessErrors($scope, data, status, null, {
                        hdr: strings.get('error.HEADER'),
                        msg: strings.get('error.CALL', { path: `${GetBasePath('tokens')}${tok.id}`, status })
                    });
                }).finally(() => {
                    Wait('stop');
                });
        };

        const deleteModalBody = `<div class="Prompt-bodyQuery">${strings.get('deleteResource.CONFIRM', 'token')}</div>`;

        Prompt({
            hdr: strings.get('deleteResource.HEADER'),
            resourceName: _.has(tok, 'summary_fields.application.name') ?
                strings.get('list.HEADER', tok.summary_fields.application.name) :
                strings.get('list.PERSONAL_ACCESS_TOKEN'),
            body: deleteModalBody,
            action,
            actionText: strings.get('add.DELETE_ACTION_LABEL')
        });
    };
}

ListTokensController.$inject = [
    '$filter',
    '$scope',
    '$state',
    'Dataset',
    'TokensStrings',
    'ProcessErrors',
    'GetBasePath',
    'Prompt',
    'Wait',
    'resolvedModels'
];

export default ListTokensController;
