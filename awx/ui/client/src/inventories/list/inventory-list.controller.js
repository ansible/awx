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
    Dataset, InventoryUpdate, canAdd) {

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
                inventory.syncTip = inventory.inventory_sources_with_failures + ' sources with sync failures. Click for details';
            }
            else {
                inventory.syncStatus = 'successful';
                inventory.syncTip = 'No inventory sync failures. Click for details.';
            }
        }
        else {
            inventory.syncStatus = 'na';
            inventory.syncTip = 'Not configured for inventory sync.';
            inventory.launch_class = "btn-disabled";
        }

        if (inventory.has_active_failures) {
            inventory.hostsStatus = 'error';
            inventory.hostsTip = inventory.hosts_with_active_failures + ' hosts with failures. Click for details.';
        }
        else if (inventory.total_hosts) {
            inventory.hostsStatus = 'successful';
            inventory.hostsTip = 'No hosts with failures. Click for details.';
        }
        else {
            inventory.hostsStatus = 'none';
            inventory.hostsTip = 'Inventory contains 0 hosts.';
        }

        inventory.kind_label = inventory.kind === '' ? 'Inventory' : (inventory.kind === 'smart' ? 'Smart Inventory': 'Inventory');
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
                    if (parseInt($state.params.inventory_id) === id) {
                        $state.go("^", null, {reload: true});
                    } else {
                       $state.go('.', null, {reload: true});
                       Wait('stop');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                    });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class="Prompt-bodyQuery">Are you sure you want to delete the inventory below?</div><div class="Prompt-bodyTarget">' + $filter('sanitize')(name) + '</div>',
            action: action,
            actionText: 'DELETE'
        });
    };

    $scope.syncInventory = function(inventory) {
        InventoryUpdate({
            scope: $scope,
            url: inventory.related.update_inventory_sources,
            updateAllSources: true
        });
    };
}

export default ['$scope',
    '$filter', 'Rest', 'InventoryList', 'Prompt',
    'ProcessErrors', 'GetBasePath', 'Wait',
    '$state', 'Dataset', 'InventoryUpdate', 'canAdd', InventoriesList
];
