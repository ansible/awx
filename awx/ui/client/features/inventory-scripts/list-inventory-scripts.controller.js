/** ***********************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 ************************************************ */

function InventoryScriptsListController (
    Dataset,
    inventoryScriptModel,
    strings,
    $scope,
    $filter,
    Alert,
    Prompt,
    Wait,
    $state,
    ProcessErrors,
    ngToast,
    InventoryScriptModel
) {
    const vm = this || {};

    vm.strings = strings;

    // smart-search
    vm.list = {
        iterator: 'inventory_script',
        name: 'inventory_scripts'
    };
    vm.dataset = Dataset.data;
    vm.inventoryScripts = Dataset.data.results;

    $scope.$watch('$state.params', () => {
        vm.activeId = _.has($state, 'params.inventory_script_id') ?
            parseInt($state.params.inventory_script_id, 10) : null;
    }, true);

    const createErrorHandler = (path, action) => ({ data, status }) => {
        const hdr = strings.get('error.HEADER');
        const msg = strings.get('error.CALL', { path, action, status });
        ProcessErrors($scope, data, status, null, { hdr, msg });
    };

    vm.getModified = inventoryScript => {
        const modified = _.get(inventoryScript, 'modified');

        if (!modified) {
            return undefined;
        }

        let html = $filter('longDate')(modified);

        const { username, id } = _.get(inventoryScript, 'summary_fields.modified_by', {});

        if (username && id) {
            html += ` by <a href="/#/users/${id}">${$filter('sanitize')(username)}</a>`;
        }

        return html;
    };

    vm.deleteInventoryScript = inventoryScript => {
        if (!inventoryScript) {
            Alert(strings.get('error.DELETE'), strings.get('alert.MISSING_PARAMETER'));
            return;
        }

        const reload = () => {
            const { page } = _.get($state.params, 'inventory_script_search');
            let reloadListStateParams = null;

            if (vm.inventoryScripts.length === 1 && page && page !== '1') {
                reloadListStateParams = _.cloneDeep($state.params);
                const previousPage = (parseInt(page, 0) - 1).toString();
                reloadListStateParams.inventory_script_search.page = previousPage;
            }

            if (parseInt($state.params.inventory_script_id, 0) === inventoryScript.id) {
                $state.go('inventoryScripts', reloadListStateParams, { reload: true });
            } else {
                $state.go('.', reloadListStateParams, { reload: true });
            }
        };

        Prompt({
            action () {
                $('#prompt-modal').modal('hide');
                Wait('start');
                new InventoryScriptModel('get', inventoryScript, true)
                    .then((resourceModel) => {
                        resourceModel.request('delete', inventoryScript.id)
                            .then(() => {
                                reload();
                            })
                            .catch(createErrorHandler('delete inventory script', 'DELETE'))
                            .finally(() => Wait('stop'));
                    });
            },
            hdr: strings.get('DELETE'),
            resourceName: $filter('sanitize')(inventoryScript.name),
            body: strings.get('deleteResource.CONFIRM', 'inventory script'),
        });
    };

    vm.copyInventoryScript = inventoryScript => {
        if (!inventoryScript) {
            Alert(strings.get('error.COPY'), strings.get('alert.MISSING_PARAMETER'));
            return;
        }

        Wait('start');
        new InventoryScriptModel('get', inventoryScript.id)
            .then((resourceModel) => {
                resourceModel.copy()
                    .then((copiedInventoryScript) => {
                        const sanitizedName = $filter('sanitize')(copiedInventoryScript.name);
                        ngToast.success({
                            content: `
                                <div class="Toast-wrapper">
                                    <div class="Toast-icon">
                                        <i class="fa fa-check-circle Toast-successIcon"></i>
                                    </div>
                                    <div>
                                        ${strings.get('SUCCESSFUL_CREATION', sanitizedName)}
                                    </div>
                                </div>`,
                            dismissButton: false,
                            dismissOnTimeout: true
                        });
                        $state.go('.', null, { reload: true });
                    })
                    .catch(createErrorHandler('copy inventory script', 'POST'))
                    .finally(() => Wait('stop'));
            });
    };
}

InventoryScriptsListController.$inject = [
    'Dataset',
    'inventoryScriptModel',
    'InventoryScriptsStrings',
    '$scope',
    '$filter',
    'Alert',
    'Prompt',
    'Wait',
    '$state',
    'ProcessErrors',
    'ngToast',
    'InventoryScriptModel'
];

export default InventoryScriptsListController;
