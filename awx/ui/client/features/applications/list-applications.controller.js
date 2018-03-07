/** ***********************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 ************************************************ */
function ListApplicationsController (
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
) {
    const vm = this || {};
    const application = resolvedModels;

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
    $scope.$on('updateDataset', (e, dataset) => {
        $scope[key] = dataset;
        $scope[name] = dataset.results;
        vm.applicationsCount = dataset.count;
    });

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

    vm.deleteApplication = app => {
        if (!app) {
            Alert(strings.get('error.DELETE'), strings.get('alert.MISSING_PARAMETER'));
            return;
        }

        application.getDependentResourceCounts(application.id)
            .then(counts => displayApplicationDeletePrompt(app, counts));
    };

    function createErrorHandler (path, action) {
        return ({ data, status }) => {
            const hdr = strings.get('error.HEADER');
            const msg = strings.get('error.CALL', { path, action, status });
            ProcessErrors($scope, data, status, null, { hdr, msg });
        };
    }

    function handleSuccessfulDelete (app) {
        const { page } = _.get($state.params, 'application_search');
        let reloadListStateParams = null;

        if ($scope.applications.length === 1 && !_.isEmpty(page) && page !== '1') {
            reloadListStateParams = _.cloneDeep($state.params);
            const pageNumber = (parseInt(reloadListStateParams.application_search.page, 0) - 1);
            reloadListStateParams.application_search.page = pageNumber.toString();
        }

        if (parseInt($state.params.application_id, 0) === app.id) {
            $state.go('applications', reloadListStateParams, { reload: true });
        } else {
            $state.go('.', reloadListStateParams, { reload: true });
        }
    }

    function displayApplicationDeletePrompt (app, counts) {
        Prompt({
            action () {
                $('#prompt-modal').modal('hide');
                Wait('start');
                application
                    .request('delete', app.id)
                    .then(() => handleSuccessfulDelete(app))
                    .catch(createErrorHandler('delete application', 'DELETE'))
                    .finally(() => Wait('stop'));
            },
            hdr: strings.get('DELETE'),
            resourceName: $filter('sanitize')(app.name),
            body: buildApplicationDeletePromptHTML(counts),
        });
    }

    function buildApplicationDeletePromptHTML (counts) {
        const buildCount = count => `<span class="badge List-titleBadge">${count}</span>`;
        const buildLabel = label => `<span class="Prompt-warningResourceTitle">
            ${$filter('sanitize')(label)}</span>`;
        const buildCountLabel = ({ count, label }) => `<div>
            ${buildLabel(label)}${buildCount(count)}</div>`;

        const displayedCounts = counts.filter(({ count }) => count > 0);

        const html = `
            ${displayedCounts.length ? strings.get('deleteResource.USED_BY', 'application') : ''}
            ${strings.get('deleteResource.CONFIRM', 'application')}
            ${displayedCounts.map(buildCountLabel).join('')}
        `;

        return html;
    }
}

ListApplicationsController.$inject = [
    '$filter',
    '$scope',
    '$state',
    'Alert',
    'Dataset',
    'ProcessErrors',
    'Prompt',
    'resolvedModels',
    'ApplicationsStrings',
    'Wait'
];

export default ListApplicationsController;
