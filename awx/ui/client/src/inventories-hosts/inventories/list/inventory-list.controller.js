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
    $filter, Rest, InventoryList, Prompt,
    ProcessErrors, GetBasePath, Wait, $state,
    Dataset, canAdd, i18n) {

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
        inventory.host_status_class = "Inventories-hostStatus";

        if (inventory.has_inventory_sources) {
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
    }

    $scope.editInventory = function (inventory) {
        if(inventory.kind && inventory.kind === 'smart') {
            $state.go('inventories.editSmartInventory', {smartinventory_id: inventory.id});
        }
        else {
            $state.go('inventories.edit', {inventory_id: inventory.id});
        }
    };

    $scope.deleteInventory = function (id, name) {
        var action = function () {
            var url = defaultUrl + id + '/';
            Wait('start');
            $('#prompt-modal').modal('hide');
            Rest.setUrl(url);
            Rest.destroy()
                .success(function () {
                    Wait('stop');
                })
                .error(function (data, status) {
                    ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                    });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class="Prompt-bodyQuery">' + i18n._('Are you sure you want to delete the inventory below?') + '</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>' +
                    '<div class="Prompt-bodyNote"><span class="Prompt-bodyNote--emphasis">Note:</span> ' + i18n._('The inventory will be in a pending status until the final delete is processed.') + '</div>',
            action: action,
            actionText: i18n._('DELETE')
        });
    };

    $scope.$on(`ws-inventories`, function(e, data){
        let inventory = $scope.inventories.find((inventory) => inventory.id === data.inventory_id);
        if (data.status === 'pending_deletion' && inventory !== undefined) {
            inventory.pending_deletion = true;
        }
        if (data.status === 'deleted') {
            let reloadListStateParams = null;

            if($scope.inventories.length === 1 && $state.params.inventory_search && !_.isEmpty($state.params.inventory_search.page) && $state.params.inventory_search.page !== '1') {
                reloadListStateParams = _.cloneDeep($state.params);
                reloadListStateParams.inventory_search.page = (parseInt(reloadListStateParams.inventory_search.page)-1).toString();
            }

            if (parseInt($state.params.inventory_id) === data.inventory_id) {
                $state.go("^", reloadListStateParams, {reload: true});
            } else {
                $state.go('.', reloadListStateParams, {reload: true});
            }
        }
    });
}

export default ['$scope',
    '$filter', 'Rest', 'InventoryList', 'Prompt',
    'ProcessErrors', 'GetBasePath', 'Wait',
    '$state', 'Dataset', 'canAdd', 'i18n', InventoriesList
];
