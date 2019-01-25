/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$rootScope', '$scope', 'Wait', 'InventoryScriptsList',
    'GetBasePath', 'Rest', 'ProcessErrors', 'Prompt', '$state', '$filter',
    'Dataset', 'rbacUiControlService', 'InventoryScriptModel', 'InventoryScriptsStrings',
    'i18n', 'ngToast',
    function(
        $rootScope, $scope, Wait, InventoryScriptsList,
        GetBasePath, Rest, ProcessErrors, Prompt, $state, $filter,
        Dataset, rbacUiControlService, InventoryScript, InventoryScriptsStrings,
        i18n, ngToast
    ) {
        let inventoryScript = new InventoryScript();
        var defaultUrl = GetBasePath('inventory_scripts'),
            list = InventoryScriptsList;

        init();

        function init() {
            $scope.canAdd = false;

            rbacUiControlService.canAdd("inventory_scripts")
                .then(function(params) {
                    $scope.canAdd = params.canAdd;
                });

            // search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        }

        // @todo what is going on here, and if it needs to happen in this controller make $rootScope var name more explicit
        if ($rootScope.addedItem) {
            $scope.addedItem = $rootScope.addedItem;
            delete $rootScope.addedItem;
        }

        $scope.editCustomInv = function() {
            $state.go('inventoryScripts.edit', {
                inventory_script_id: this.inventory_script.id
            });
        };

        $scope.copyCustomInv = inventoryScript => {
            Wait('start');
            new InventoryScript('get', inventoryScript.id)
                .then(model => model.copy())
                .then((copiedInvScript) => {
                    ngToast.success({
                        content: `
                            <div class="Toast-wrapper">
                                <div class="Toast-icon">
                                    <i class="fa fa-check-circle Toast-successIcon"></i>
                                </div>
                                <div>
                                    ${InventoryScriptsStrings.get('SUCCESSFUL_CREATION', copiedInvScript.name)}
                                </div>
                            </div>`,
                        dismissButton: false,
                        dismissOnTimeout: true
                    });
                    $state.go('.', null, { reload: true });
                })
                .catch(({ data, status }) => {
                    const params = { hdr: 'Error!', msg: `Call to copy failed. Return status: ${status}` };
                    ProcessErrors($scope, data, status, null, params);
                })
                .finally(() => Wait('stop'));
        };

        $scope.deleteCustomInv = function(id, name) {

            var action = function() {
                $('#prompt-modal').modal('hide');
                Wait('start');
                var url = defaultUrl + id + '/';
                inventoryScript.request('delete', id)
                    .then(() => {

                        let reloadListStateParams = null;

                        if($scope.inventory_scripts.length === 1 && $state.params.inventory_script_search && _.has($state, 'params.inventory_script_search.page') && $state.params.inventory_script_search.page !== '1') {
                            reloadListStateParams = _.cloneDeep($state.params);
                            reloadListStateParams.inventory_script_search.page = (parseInt(reloadListStateParams.inventory_script_search.page)-1).toString();
                        }

                        if (parseInt($state.params.inventory_script_id) === id) {
                            $state.go('^', reloadListStateParams, { reload: true });
                        } else {
                            $state.go('.', reloadListStateParams, { reload: true });
                        }
                    })
                    .catch(({data, status}) => {
                        ProcessErrors($scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                        });
                    });
            };

            inventoryScript.getDependentResourceCounts(id)
                .then((counts) => {
                    const invalidateRelatedLines = [];
                    let deleteModalBody = `<div class="Prompt-bodyQuery">${InventoryScriptsStrings.get('deleteResource.CONFIRM', 'inventory script')}</div>`;

                    counts.forEach(countObj => {
                        if(countObj.count && countObj.count > 0) {
                            invalidateRelatedLines.push(`<div><span class="Prompt-warningResourceTitle">${countObj.label}</span><span class="badge List-titleBadge">${countObj.count}</span></div>`);
                        }
                    });

                    if (invalidateRelatedLines && invalidateRelatedLines.length > 0) {
                        deleteModalBody = `<div class="Prompt-bodyQuery">${InventoryScriptsStrings.get('deleteResource.USED_BY', 'inventory script')} ${InventoryScriptsStrings.get('deleteResource.CONFIRM', 'inventory script')}</div>`;
                        invalidateRelatedLines.forEach(invalidateRelatedLine => {
                            deleteModalBody += invalidateRelatedLine;
                        });
                    }

                    Prompt({
                        hdr: i18n._('Delete'),
                        resourceName: $filter('sanitize')(name),
                        body: deleteModalBody,
                        action: action,
                        actionText: i18n._('DELETE')
                    });
                });
        };

        $scope.addCustomInv = function() {
            $state.go('inventoryScripts.add');
        };

    }
];
