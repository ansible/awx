/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 export default
    ['$scope', '$rootScope', '$state', '$stateParams', 'NestedGroupListDefinition', 'InventoryUpdate',
    'GroupManageService', 'CancelSourceUpdate', 'rbacUiControlService', 'GetBasePath',
    'GetHostsStatusMsg', 'Dataset', 'Find', 'QuerySet', 'inventoryData',
    function($scope, $rootScope, $state, $stateParams, NestedGroupListDefinition, InventoryUpdate,
        GroupManageService, CancelSourceUpdate, rbacUiControlService, GetBasePath,
        GetHostsStatusMsg, Dataset, Find, qs, inventoryData){

        let list = NestedGroupListDefinition;

        init();

        function init(){
        $scope.inventory_id = $stateParams.inventory_id;
        $scope.canAdhoc = inventoryData.summary_fields.user_capabilities.adhoc;
        $scope.canAdd = false;

        rbacUiControlService.canAdd(GetBasePath('inventory') + $scope.inventory_id + "/groups")
            .then(function(canAdd) {
                $scope.canAdd = canAdd;
            });

            // Search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            if($state.current.name === "inventories.edit.groups.edit.nested_groups.edit") {
                $scope.rowBeingEdited = $state.params.group_id;
                $scope.listBeingEdited = "groups";
            }

            $scope.inventory_id = $stateParams.inventory_id;
            _.forEach($scope[list.name], buildStatusIndicators);

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

        $scope.createGroup = function(){
            $state.go('inventories.edit.groups.edit.nested_groups.add');
        };

        $scope.editGroup = function(id){
            $state.go('inventories.edit.groups.edit', {group_id: id});
        };

        var cleanUpStateChangeListener = $rootScope.$on('$stateChangeSuccess', function(event, toState, toParams) {
             if (toState.name === "inventories.edit.groups.edit.nested_groups.edit") {
                 $scope.rowBeingEdited = toParams.group_id;
                 $scope.listBeingEdited = "groups";
             }
             else {
                 delete $scope.rowBeingEdited;
                 delete $scope.listBeingEdited;
             }
        });

        // Remove the listener when the scope is destroyed to avoid a memory leak
        $scope.$on('$destroy', function() {
            cleanUpStateChangeListener();
        });

        $scope.setAdhocPattern = function(){
            var pattern = _($scope.groupsSelected)
                .map(function(item){
                    return item.name;
                }).value().join(':');

            $state.go('^.^.^.adhoc', {pattern: pattern});
        };

    }];
