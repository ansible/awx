/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', 'NestedHostsListDefinition', '$rootScope', 'GetBasePath',
    'rbacUiControlService', 'Dataset', '$state', '$filter', 'Prompt', 'Wait',
    'HostsService', 'SetStatus', 'canAdd', 'GroupsService', 'ProcessErrors', 'groupData', 'inventoryData', 'InventoryHostsStrings',
    '$transitions',
    function($scope, NestedHostsListDefinition, $rootScope, GetBasePath,
    rbacUiControlService, Dataset, $state, $filter, Prompt, Wait,
    HostsService, SetStatus, canAdd, GroupsService, ProcessErrors, groupData, inventoryData, InventoryHostsStrings,
    $transitions) {

    let list = NestedHostsListDefinition;

    init();

    function init(){
        $scope.canAdd = canAdd;
        $scope.enableSmartInventoryButton = false;
        $scope.disassociateFrom = groupData;
        $scope.smartInventoryButtonTooltip = InventoryHostsStrings.get('smartinventorybutton.DISABLED_INSTRUCTIONS');

        // Search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        $scope.inventory_obj = inventoryData;

        $rootScope.flashMessage = null;

        $scope.$watchCollection(list.name, function() {
            $scope[list.name] = _.map($scope.nested_hosts, function(value) {
                angular.forEach(value.summary_fields.groups.results, function(directParentGroup) {
                    if(directParentGroup.id === parseInt($state.params.group_id)) {
                        value.can_disassociate = true;
                    }
                });
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
        _.forEach($scope.nested_hosts, function(value) {
            SetStatus({
                scope: $scope,
                host: value
            });
        });
    }

    $scope.associateHost = function(){
        $state.go('inventories.edit.groups.edit.nested_hosts.associate');
    };
    $scope.editHost = function(id){
        $state.go('inventories.edit.hosts.edit', {host_id: id});
    };
    $scope.disassociateHost = function(host){
        $scope.toDisassociate = {};
        angular.extend($scope.toDisassociate, host);
        $('#host-disassociate-modal').modal('show');
    };

    $scope.confirmDisassociate = function(){

        // Bind an even listener for the modal closing.  Trying to $state.go() before the modal closes
        // will mean that these two things are running async and the modal may not finish closing before
        // the state finishes transitioning.
        $('#host-disassociate-modal').off('hidden.bs.modal').on('hidden.bs.modal', function () {
            // Remove the event handler so that we don't end up with multiple bindings
            $('#host-disassociate-modal').off('hidden.bs.modal');

            let reloadListStateParams = null;

            if($scope.nested_hosts.length === 1 && $state.params.nested_host_search && !_.isEmpty($state.params.nested_host_search.page) && $state.params.nested_host_search.page !== '1') {
                reloadListStateParams = _.cloneDeep($state.params);
                reloadListStateParams.nested_host_search.page = (parseInt(reloadListStateParams.nested_host_search.page)-1).toString();
            }

            // Reload the inventory manage page and show that the group has been removed
            $state.go('.', reloadListStateParams, {reload: true});
        });

        let closeModal = function(){
            $('#host-disassociate-modal').modal('hide');
            $('body').removeClass('modal-open');
            $('.modal-backdrop').remove();
        };

        GroupsService.disassociateHost($scope.toDisassociate.id, $scope.disassociateFrom.id)
            .then(() => {
                closeModal();
            }).catch((error) => {
                closeModal();
                ProcessErrors(null, error.data, error.status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to disassociate host from group: POST returned status' +
                        error.status
                });
            });
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

    $scope.setAdhocPattern = function(){
        var pattern = _($scope.hostsSelected)
            .map(function(item){
                return item.name;
            }).value().join(':');

        $state.go('inventories.edit.adhoc', {pattern: pattern});
    };
}];
