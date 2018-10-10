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
    const key = 'token_dataset';

    $scope.list = { iterator, name, basePath: 'tokens' };
    $scope.collection = { iterator };
    $scope[key] = Dataset.data;
    vm.tokensCount = Dataset.data.count;
    $scope[name] = Dataset.data.results;
    $scope.$on('updateDataset', (e, dataset) => {
        $scope[key] = dataset;
        $scope[name] = dataset.results;
        vm.tokensCount = dataset.count;
    });

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

                    if ($scope.tokens.length === 1 && $state.params.token_search &&
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
