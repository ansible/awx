/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 export default
    ['$scope', '$rootScope', '$state', '$stateParams', 'HostNestedGroupListDefinition', 'InventoryUpdate',
    'GroupsService', 'CancelSourceUpdate', 'rbacUiControlService', 'GetBasePath',
    'Dataset', 'Find', 'QuerySet', 'inventoryData', 'canAdd', 'ProcessErrors', 'host',
    function($scope, $rootScope, $state, $stateParams, HostNestedGroupListDefinition, InventoryUpdate,
        GroupsService, CancelSourceUpdate, rbacUiControlService, GetBasePath,
        Dataset, Find, qs, inventoryData, canAdd, ProcessErrors, host){

        let list = HostNestedGroupListDefinition;

        init();

        function init(){
            $scope.toDisassociate = host;
            $scope.inventory_id = $stateParams.inventory_id;
            $scope.canAdhoc = inventoryData.summary_fields.user_capabilities.adhoc;
            $scope.canAdd = canAdd;

            // Search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $scope.$on('selectedOrDeselected', function(e, value) {
                let item = value.value;

                if (value.isSelected) {
                    if(!$scope.groupsSelected) {
                        $scope.groupsSelected = [];
                    }
                    $scope.groupsSelected.push(item);
                } else {
                    _.remove($scope.groupsSelected, { id: item.id });
                    if($scope.groupsSelected.length === 0) {
                        $scope.groupsSelected = null;
                    }
                }
            });

        }

        $scope.associateGroup = function() {
            $state.go('.associate');
        };

        $scope.disassociateGroup = function(group){
            $scope.disassociateFrom = group;
            $('#group-disassociate-modal').modal('show');
        };

        $scope.confirmDisassociate = function(){

            // Bind an even listener for the modal closing.  Trying to $state.go() before the modal closes
            // will mean that these two things are running async and the modal may not finish closing before
            // the state finishes transitioning.
            $('#group-disassociate-modal').off('hidden.bs.modal').on('hidden.bs.modal', function () {
                // Remove the event handler so that we don't end up with multiple bindings
                $('#group-disassociate-modal').off('hidden.bs.modal');

                let reloadListStateParams = null;

                if($scope.nested_groups.length === 1 && $state.params.nested_group_search && !_.isEmpty($state.params.nested_group_search.page) && $state.params.nested_group_search.page !== '1') {
                    reloadListStateParams = _.cloneDeep($state.params);
                    reloadListStateParams.nested_group_search.page = (parseInt(reloadListStateParams.nested_group_search.page)-1).toString();
                }

                // Reload the inventory manage page and show that the group has been removed
                $state.go('.', reloadListStateParams, {reload: true});
            });

            let closeModal = function(){
                $('#group-disassociate-modal').modal('hide');
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
                        msg: 'Failed to disassociate group from parent group: POST returned status' +
                            error.status
                    });
                });
        };

        $scope.editGroup = function(id){
            $state.go('inventories.edit.groups.edit', {group_id: id});
        };

        $scope.goToGroupGroups = function(id){
            $state.go('inventories.edit.groups.edit.nested_groups', {group_id: id});
        };

        $scope.setAdhocPattern = function(){
            var pattern = _($scope.groupsSelected)
                .map(function(item){
                    return item.name;
                }).value().join(':');

            $state.go('^.^.^.adhoc', {pattern: pattern});
        };

    }];
