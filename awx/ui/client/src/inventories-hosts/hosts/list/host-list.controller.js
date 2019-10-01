/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


function HostsList($scope, HostsList, $rootScope, GetBasePath,
    rbacUiControlService, Dataset, $state, $filter, Prompt, Wait,
    HostsService, SetStatus, canAdd, $transitions, InventoryHostsStrings) {

    let list = HostsList;

    init();

    function init(){
        $scope.canAdd = canAdd;
        $scope.enableSmartInventoryButton = false;
        $scope.smartInventoryButtonTooltip = InventoryHostsStrings.get('smartinventorybutton.DISABLED_INSTRUCTIONS');
        $scope.strings = InventoryHostsStrings;

        // Search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $rootScope.flashMessage = null;

        $scope.$watchCollection(list.name, function() {
            $scope[list.name] = _.map($scope.hosts, function(value) {
                value.inventory_name = value.summary_fields.inventory.name;
                value.inventory_id = value.summary_fields.inventory.id;
                return value;
            });
            setJobStatus();
        });

        $transitions.onSuccess({}, function(trans) {
            if(trans.params('to') && trans.params('to').host_search) {
                let hasMoreThanDefaultKeys = false;
                angular.forEach(trans.params('to').host_search, function(value, key) {
                    if(key !== 'order_by' && key !== 'page_size' && key !== 'page') {
                        hasMoreThanDefaultKeys = true;
                    }
                });
                $scope.enableSmartInventoryButton = hasMoreThanDefaultKeys ? true : false;
                $scope.smartInventoryButtonTooltip = hasMoreThanDefaultKeys ? InventoryHostsStrings.get('smartinventorybutton.ENABLED_INSTRUCTIONS') : InventoryHostsStrings.get('smartinventorybutton.DISABLED_INSTRUCTIONS');
            }
            else {
                $scope.enableSmartInventoryButton = false;
                $scope.smartInventoryButtonTooltip = InventoryHostsStrings.get('smartinventorybutton.DISABLED_INSTRUCTIONS');
            }
        });

    }

    function setJobStatus(){
        _.forEach($scope.hosts, function(value) {
            SetStatus({
                scope: $scope,
                host: value
            });
        });
    }

    $scope.createHost = function(){
        $state.go('hosts.add');
    };
    $scope.editHost = function(id){
        $state.go('hosts.edit', {host_id: id});
    };
    $scope.goToInsights = function(id){
        $state.go('hosts.edit.insights', {host_id:id});
    };
    $scope.toggleHost = function(event, host) {
        try {
            $(event.target).tooltip('hide');
        } catch (e) {
            // ignore
        }

        host.enabled = !host.enabled;
        HostsService.patch(host.id, {
            enabled: host.enabled
        });
    };

    $scope.smartInventory = function() {
        $state.go('inventories.addSmartInventory', {hostfilter: JSON.stringify({"host_filter":`${$state.params.host_search.host_filter}`})});
    };

    $scope.editInventory = function(host) {
        if(host.summary_fields && host.summary_fields.inventory) {
            if(host.summary_fields.inventory.kind && host.summary_fields.inventory.kind === 'smart') {
                $state.go('inventories.editSmartInventory', {smartinventory_id: host.inventory});
            }
            else {
                $state.go('inventories.edit', {inventory_id: host.inventory});
            }
        }
    };

}

export default ['$scope', 'HostsList', '$rootScope', 'GetBasePath',
    'rbacUiControlService', 'Dataset', '$state', '$filter', 'Prompt', 'Wait',
    'HostsService', 'SetStatus', 'canAdd', '$transitions', 'InventoryHostsStrings', HostsList
];
