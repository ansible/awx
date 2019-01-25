/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import HostsService from './../hosts/host.service';
export default ['$scope', 'ListDefinition', '$rootScope', 'GetBasePath',
    'rbacUiControlService', 'Dataset', '$state', '$filter', 'Prompt', 'Wait',
    'HostsService', 'SetStatus', 'canAdd', 'i18n', 'InventoryHostsStrings', '$transitions',
    function($scope, ListDefinition, $rootScope, GetBasePath,
    rbacUiControlService, Dataset, $state, $filter, Prompt, Wait,
    HostsService, SetStatus, canAdd, i18n, InventoryHostsStrings, $transitions) {

    let list = ListDefinition;

    init();

    function init(){
        $scope.canAdd = canAdd;
        $scope.enableSmartInventoryButton = false;
        $scope.smartInventoryButtonTooltip = InventoryHostsStrings.get('smartinventorybutton.DISABLED_INSTRUCTIONS');

        // Search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $rootScope.flashMessage = null;

        $scope.$watchCollection(list.name, function() {
            $scope[list.name] = _.map($scope.hosts, function(value) {
                value.inventory_name = value.summary_fields.inventory.name;
                value.inventory_id = value.summary_fields.inventory.id;
                angular.forEach($scope.hostsSelected, function(selectedHost){
                    if(selectedHost.id === value.id) {
                        value.isSelected = true;
                    }
                });
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

        $scope.$on('selectedOrDeselected', function(e, value) {
            let item = value.value;

            if (value.isSelected) {
                if(!$scope.hostsSelected) {
                    $scope.hostsSelected = [];
                }
                $scope.hostsSelected.push(item);
            } else {
                _.remove($scope.hostsSelected, { id: item.id });
                if($scope.hostsSelected.length === 0) {
                    $scope.hostsSelected = null;
                }
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
        $state.go('inventories.edit.hosts.add');
    };
    $scope.editHost = function(host){
        if($state.includes('inventories.edit.hosts')) {
            $state.go('inventories.edit.hosts.edit', {host_id: host.id});
        }
        else if($state.includes('inventories.editSmartInventory.hosts')) {
            $state.go('inventories.editSmartInventory.hosts.edit', {host_id: host.id});
        }
    };
    $scope.goToInsights = function(host){
        $state.go('inventories.edit.hosts.edit.insights', {inventory_id: host.inventory_id, host_id:host.id});
    };
    $scope.deleteHost = function(id, name){
        var body = '<div class=\"Prompt-bodyQuery\">' + i18n._('Are you sure you want to permanently delete the host below from the inventory?') + '</div><div class=\"Prompt-bodyTarget\">' + $filter('sanitize')(name) + '</div>';
        var action = function(){
            delete $rootScope.promptActionBtnClass;
            Wait('start');
            HostsService.delete(id).then(() => {
                $('#prompt-modal').modal('hide');

                let reloadListStateParams = null;

                if($scope.hosts.length === 1 && $state.params.host_search && _.has($state, 'params.host_search.page') && $state.params.host_search.page !== '1') {
                    reloadListStateParams = _.cloneDeep($state.params);
                    reloadListStateParams.host_search.page = (parseInt(reloadListStateParams.host_search.page)-1).toString();
                }

                if (parseInt($state.params.host_id) === id) {
                    $state.go('^', reloadListStateParams, {reload: true});
                } else {
                    $state.go('.', reloadListStateParams, {reload: true});
                }
                Wait('stop');
            });
        };
        // Prompt depends on having $rootScope.promptActionBtnClass available...
        Prompt({
            hdr: i18n._('Delete Host'),
            body: body,
            action: action,
            actionText: i18n._('DELETE'),
        });
        $rootScope.promptActionBtnClass = 'Modal-errorButton';
    };

    $scope.toggleHost = function(event, host) {
        try {
            $(event.target).tooltip('hide');
        } catch (e) {
            // ignore
        }

        host.enabled = !host.enabled;

        HostsService.put(host).then(function(){
            $state.go($state.current, null, {reload: true});
        });
    };

    $scope.smartInventory = function() {
        $state.go('inventories.addSmartInventory');
    };

    $scope.setAdhocPattern = function(){
        var pattern = _($scope.hostsSelected)
            .map(function(item){
                return item.name;
            }).value().join(':');

        if($state.includes('inventories.edit')) {
            $state.go('inventories.edit.adhoc', {pattern: pattern});
        }
        else if($state.includes('inventories.editSmartInventory')) {
            $state.go('inventories.editSmartInventory.adhoc', {pattern: pattern});
        }
    };
}];
