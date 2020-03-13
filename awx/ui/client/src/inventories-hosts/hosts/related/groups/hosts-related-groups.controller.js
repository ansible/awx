/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 export default
    ['$scope', '$rootScope', '$state', '$stateParams', 'HostsRelatedGroupsList', 'InventoryHostsStrings',
    'CancelSourceUpdate', 'rbacUiControlService', 'GetBasePath', 'Dataset', 'Find', 'QuerySet', 'inventoryData', 'host', 'GroupsService',
    function($scope, $rootScope, $state, $stateParams, HostsRelatedGroupsList, InventoryHostsStrings,
        CancelSourceUpdate, rbacUiControlService, GetBasePath, Dataset, Find, qs, inventoryData, host, GroupsService){

        let list = HostsRelatedGroupsList;

        init();

        function init(){
            $scope.inventory_id = inventoryData.id;
            $scope.canAdd = false;
            $scope.strings = InventoryHostsStrings;

            rbacUiControlService.canAdd(GetBasePath('inventory') + $scope.inventory_id + "/groups")
                .then(function(canAdd) {
                    $scope.canAdd = canAdd;
                });

            // Search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

        }

        $scope.editGroup = function(id){
            $state.go('inventories.edit.groups.edit', {inventory_id: $scope.inventory_id, group_id: id});
        };

        $scope.goToGroupGroups = function(id){
            $state.go('inventories.edit.groups.edit.nested_groups', {inventory_id: $scope.inventory_id, group_id: id});
        };

        $scope.associateGroup = function() {
            $state.go('.associate', {inventory_id: $scope.inventory_id});
        };

        $scope.disassociateHost = function(group){
            $scope.disassociateGroup = {};
            angular.extend($scope.disassociateGroup, group);
            $('#host-disassociate-modal').modal('show');
        };

        $scope.confirmDisassociate = function(){

            $('#host-disassociate-modal').off('hidden.bs.modal').on('hidden.bs.modal', function () {
                $('#host-disassociate-modal').off('hidden.bs.modal');

                let reloadListStateParams = null;

                if($scope.groups.length === 1 && $state.params.group_search && !_.isEmpty($state.params.group_search.page) && $state.params.group_search.page !== '1') {
                    reloadListStateParams = _.cloneDeep($state.params);
                    reloadListStateParams.group_search.page = (parseInt(reloadListStateParams.group_search.page)-1).toString();
                }

                $state.go('.', reloadListStateParams, {reload: true});
            });

            GroupsService.disassociateHost(host.id, $scope.disassociateGroup.id).then(() => {
                $state.go($state.current, null, {reload: true});
                $('#host-disassociate-modal').modal('hide');
                $('body').removeClass('modal-open');
                $('.modal-backdrop').remove();
            });

        };
    }];
