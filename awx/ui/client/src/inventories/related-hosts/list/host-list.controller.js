/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import HostManageService from './../hosts/host.service';
export default ['$scope', 'RelatedHostsListDefinition', '$rootScope', 'GetBasePath',
    'rbacUiControlService', 'Dataset', '$state', '$filter', 'Prompt', 'Wait',
    'HostManageService', 'SetStatus',
    function($scope, RelatedHostsListDefinition, $rootScope, GetBasePath,
    rbacUiControlService, Dataset, $state, $filter, Prompt, Wait,
    HostManageService, SetStatus) {

    let list = RelatedHostsListDefinition;

    init();

    function init(){
        $scope.canAdd = false;
        $scope.enableSmartInventoryButton = false;

        rbacUiControlService.canAdd('hosts')
            .then(function(canAdd) {
                $scope.canAdd = canAdd;
            });

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

        $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams) {
            if(toState.name === 'hosts.addSmartInventory') {
                $scope.enableSmartInventoryButton = false;
            }
            else {
                if(toParams && toParams.host_search) {
                    let hasMoreThanDefaultKeys = false;
                    angular.forEach(toParams.host_search, function(value, key) {
                        if(key !== 'order_by' && key !== 'page_size') {
                            hasMoreThanDefaultKeys = true;
                        }
                    });
                    $scope.enableSmartInventoryButton = hasMoreThanDefaultKeys ? true : false;
                }
                else {
                    $scope.enableSmartInventoryButton = false;
                }
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

            $scope.systemTrackingDisabled = ($scope.hostsSelected && $scope.hostsSelected.length > 2) ? true : false;
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
    $scope.editHost = function(id){
        $state.go('inventories.edit.hosts.edit', {host_id: id});
    };
    $scope.deleteHost = function(id, name){
        var body = '<div class=\"Prompt-bodyQuery\">Are you sure you want to permanently delete the host below from the inventory?</div><div class=\"Prompt-bodyTarget\">' + $filter('sanitize')(name) + '</div>';
        var action = function(){
            delete $rootScope.promptActionBtnClass;
            Wait('start');
            HostManageService.delete(id).then(() => {
                $('#prompt-modal').modal('hide');
                if (parseInt($state.params.host_id) === id) {
                    $state.go("hosts", null, {reload: true});
                } else {
                    $state.go($state.current.name, null, {reload: true});
                }
                Wait('stop');
            });
        };
        // Prompt depends on having $rootScope.promptActionBtnClass available...
        Prompt({
            hdr: 'Delete Host',
            body: body,
            action: action,
            actionText: 'DELETE',
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

        HostManageService.put(host).then(function(){
            $state.go($state.current, null, {reload: true});
        });
    };

    $scope.smartInventory = function() {
        $state.go('inventories.addSmartInventory');
    };

    $scope.systemTracking = function(){
        var hostIds = _.map($scope.hostsSelected, (host) => host.id);
        $state.go('systemTracking', {
            inventoryId: $state.params.inventory_id,
            hosts: $scope.hostsSelected,
            hostIds: hostIds
        });
    };

    $scope.setAdhocPattern = function(){
        var pattern = _($scope.hostsSelected)
            .map(function(item){
                return item.name;
            }).value().join(':');

        $state.go('^.adhoc', {pattern: pattern});
    };

    $scope.copyMoveHost = function(id) {
        $state.go('inventories.edit.hosts.copyMoveHost', {host_id: id});
    };
}];
