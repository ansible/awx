/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Inventories
 * @description This controller's for the Inventory page
 */

function InventoriesList($scope,
    $filter, qs, InventoryList, Prompt,
    ProcessErrors, GetBasePath, Wait, $state,
    Dataset, canAdd, i18n, Inventory, InventoryHostsStrings,
    ngToast) {

    let inventory = new Inventory();

    let list = InventoryList,
        defaultUrl = GetBasePath('inventory');

    init();

    function init(){
        $scope.canAddInventory = canAdd;

        $scope.$watchCollection(list.name, function(){
            _.forEach($scope[list.name], processInventoryRow);
        });

        // Search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
    }

    function processInventoryRow(inventory) {
        inventory.launch_class = "";

        if (inventory.has_inventory_sources) {
            inventory.copyTip = i18n._('Inventories with sources cannot be copied');
            inventory.copyClass = "btn-disabled";
            if (inventory.inventory_sources_with_failures > 0) {
                inventory.syncStatus = 'error';
                inventory.syncTip = inventory.inventory_sources_with_failures + i18n._(' sources with sync failures. Click for details');
            }
            else {
                inventory.syncStatus = 'successful';
                inventory.syncTip = i18n._('No inventory sync failures. Click for details.');
            }
        }
        else {
            inventory.copyTip = i18n._('Copy Inventory');
            inventory.copyClass = "";
            inventory.syncStatus = 'na';
            inventory.syncTip = i18n._('Not configured for inventory sync.');
            inventory.launch_class = "btn-disabled";
        }

        if (inventory.has_active_failures) {
            inventory.hostsStatus = 'error';
            inventory.hostsTip = inventory.hosts_with_active_failures + i18n._(' hosts with failures. Click for details.');
        }
        else if (inventory.total_hosts) {
            inventory.hostsStatus = 'successful';
            inventory.hostsTip = i18n._('No hosts with failures. Click for details.');
        }
        else {
            inventory.hostsStatus = 'none';
            inventory.hostsTip = i18n._('Inventory contains 0 hosts.');
        }

        inventory.kind_label = inventory.kind === '' ? 'Inventory' : (inventory.kind === 'smart' ? i18n._('Smart Inventory'): i18n._('Inventory'));

        inventory.linkToDetails = (inventory.kind && inventory.kind === 'smart') ? `inventories.editSmartInventory({smartinventory_id:${inventory.id}})` : `inventories.edit({inventory_id:${inventory.id}})`;
    }

    $scope.copyInventory = inventory => {
        if (!inventory.has_inventory_sources) {
            Wait('start');
            new Inventory('get', inventory.id)
                .then(model => model.copy())
                .then(copiedInv => {
                    ngToast.success({
                        content: `
                            <div class="Toast-wrapper">
                                <div class="Toast-icon">
                                    <i class="fa fa-check-circle Toast-successIcon"></i>
                                </div>
                                <div>
                                    ${InventoryHostsStrings.get('SUCCESSFUL_CREATION', copiedInv.name)}
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
        }
    };

    $scope.editInventory = function (inventory, reload) {
        const goOptions = reload ? { reload: true } : null;
        if(inventory.kind && inventory.kind === 'smart') {
            $state.go('inventories.editSmartInventory', {smartinventory_id: inventory.id}, goOptions);
        }
        else {
            $state.go('inventories.edit', {inventory_id: inventory.id}, goOptions);
        }
    };

    $scope.deleteInventory = function (id, name) {
        var action = function () {
            var url = defaultUrl + id + '/';
            Wait('start');
            $('#prompt-modal').modal('hide');
            inventory.request('delete', id)
                .then(() => {
                    Wait('stop');
                })
                .catch(({data, status}) => {
                    ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                    });
                });
        };

        inventory.getDependentResourceCounts(id)
            .then((counts) => {
                const invalidateRelatedLines = [];
                let deleteModalBody = `<div class="Prompt-bodyQuery">${InventoryHostsStrings.get('deleteResource.CONFIRM', 'inventory')}</div>`;

                counts.forEach(countObj => {
                    if(countObj.count && countObj.count > 0) {
                        invalidateRelatedLines.push(`<div><span class="Prompt-warningResourceTitle">${countObj.label}</span><span class="badge List-titleBadge">${countObj.count}</span></div>`);
                    }
                });

                if (invalidateRelatedLines && invalidateRelatedLines.length > 0) {
                    deleteModalBody = `<div class="Prompt-bodyQuery">${InventoryHostsStrings.get('deleteResource.USED_BY', 'inventory')} ${InventoryHostsStrings.get('deleteResource.CONFIRM', 'inventory')}</div>`;
                    invalidateRelatedLines.forEach(invalidateRelatedLine => {
                        deleteModalBody += invalidateRelatedLine;
                    });
                }

                deleteModalBody += '<div class="Prompt-bodyNote"><span class="Prompt-bodyNote--emphasis">Note:</span> ' + i18n._('The inventory will be in a pending status until the final delete is processed.') + '</div>';

                Prompt({
                    hdr: i18n._('Delete'),
                    resourceName: $filter('sanitize')(name),
                    body: deleteModalBody,
                    action: action,
                    actionText: i18n._('DELETE')
                });
            });
    };

    $scope.$on(`ws-inventories`, function(e, data){
        let inventory = $scope.inventories.find((inventory) => inventory.id === data.inventory_id);
        if (data.status === 'pending_deletion' && inventory !== undefined) {
            inventory.pending_deletion = true;
        }
        if (data.status === 'deleted') {
            let reloadListStateParams = _.cloneDeep($state.params);

            if($scope.inventories.length === 1 && $state.params.inventory_search && _.hasIn($state, 'params.inventory_search.page') && $state.params.inventory_search.page !== '1') {
                reloadListStateParams.inventory_search.page = (parseInt(reloadListStateParams.inventory_search.page)-1).toString();
            }

            if (parseInt($state.params.inventory_id) === data.inventory_id || parseInt($state.params.smartinventory_id) === data.inventory_id) {
                $state.go("inventories", reloadListStateParams, {reload: true});
            } else {
                Wait('start');
                $state.go('.', reloadListStateParams);
                const path = GetBasePath($scope.list.basePath) || GetBasePath($scope.list.name);
                qs.search(path, reloadListStateParams.inventory_search)
                    .then((searchResponse) => {
                        $scope.inventories_dataset = searchResponse.data;
                        $scope.inventories = searchResponse.data.results;
                    })
                    .finally(() => Wait('stop'));
            }
        }
    });
}

export default ['$scope',
    '$filter', 'QuerySet', 'InventoryList', 'Prompt',
    'ProcessErrors', 'GetBasePath', 'Wait',
    '$state', 'Dataset', 'canAdd', 'i18n', 'InventoryModel',
    'InventoryHostsStrings', 'ngToast', InventoriesList
];
