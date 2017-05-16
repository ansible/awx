/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 export default
    ['$scope', '$rootScope', '$state', '$stateParams', 'HostGroupsList', 'InventoryUpdate',
    'HostManageService', 'CancelSourceUpdate', 'rbacUiControlService', 'GetBasePath',
    'GetHostsStatusMsg', 'Dataset', 'Find', 'QuerySet', 'inventoryData', 'host',
    function($scope, $rootScope, $state, $stateParams, HostGroupsList, InventoryUpdate,
        HostManageService, CancelSourceUpdate, rbacUiControlService, GetBasePath,
        GetHostsStatusMsg, Dataset, Find, qs, inventoryData, host){

        let list = HostGroupsList;

        init();

        function init(){
            $scope.inventory_id = inventoryData.id;
            $scope.canAdd = false;

            rbacUiControlService.canAdd(GetBasePath('inventory') + $scope.inventory_id + "/groups")
                .then(function(canAdd) {
                    $scope.canAdd = canAdd;
                });

            // Search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            $scope.$watchCollection(list.name, function(){
                _.forEach($scope[list.name], buildStatusIndicators);
            });
        }

        function buildStatusIndicators(group){
            if (group === undefined || group === null) {
                group = {};
            }

            let hosts_status;

            hosts_status = GetHostsStatusMsg({
                active_failures: group.hosts_with_active_failures,
                total_hosts: group.total_hosts,
                inventory_id: $scope.inventory_id,
                group_id: group.id
            });
            _.assign(group,
                {hosts_status_tip: hosts_status.tooltip},
                {hosts_status_class: hosts_status.class});
        }

        $scope.editGroup = function(id){
            $state.go('inventories.edit.groups.edit', {inventory_id: $scope.inventory_id, group_id: id});
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
                $state.go('.', null, {reload: true});
            });

            HostManageService.disassociateGroup(host, $scope.disassociateGroup.id).then(() => {
                $state.go($state.current, null, {reload: true});
                $('#host-disassociate-modal').modal('hide');
                $('body').removeClass('modal-open');
                $('.modal-backdrop').remove();
            });

        };
    }];
