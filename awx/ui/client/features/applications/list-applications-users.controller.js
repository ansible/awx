/** ***********************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 ************************************************ */
function ListApplicationsUsersController (
    $filter,
    $scope,
    Dataset,
    resolvedModels,
    strings,
    $stateParams,
    GetBasePath
) {
    const vm = this || {};
    // const application = resolvedModels;

    vm.strings = strings;
    // smart-search
    const name = 'users';
    const iterator = 'user';
    const key = 'user_dataset';

    $scope.list = { iterator, name, basePath: 'applications' };
    $scope.collection = { iterator };
    $scope.tokenBasePath = `${GetBasePath('applications')}${$stateParams.application_id}/tokens`;
    $scope[key] = Dataset.data;
    vm.usersCount = Dataset.data.count;
    $scope[name] = Dataset.data.results;
    $scope.$on('updateDataset', (e, dataset) => {
        $scope[key] = dataset;
        $scope[name] = dataset.results;
        vm.usersCount = dataset.count;
    });

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
    'resolvedModels',
    'ApplicationsStrings',
    '$stateParams',
    'GetBasePath'
];

export default ListApplicationsUsersController;
