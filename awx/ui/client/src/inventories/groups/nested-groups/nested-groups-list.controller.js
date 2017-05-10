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
        // $scope.editGroup = function(id){
        //     $state.go('inventories.edit.groups.edit.nested_groups.edit', {nested_group_id: id});
        // };
        $scope.deleteGroup = function(group){
            $scope.toDelete = {};
            angular.extend($scope.toDelete, group);
            if($scope.toDelete.total_groups === 0 && $scope.toDelete.total_hosts === 0) {
                // This group doesn't have any child groups or hosts - the user is just trying to delete
                // the group
                $scope.deleteOption = "delete";
            }
            $('#group-delete-modal').modal('show');
        };
        $scope.confirmDelete = function(){

            // Bind an even listener for the modal closing.  Trying to $state.go() before the modal closes
            // will mean that these two things are running async and the modal may not finish closing before
            // the state finishes transitioning.
            $('#group-delete-modal').off('hidden.bs.modal').on('hidden.bs.modal', function () {
                // Remove the event handler so that we don't end up with multiple bindings
                $('#group-delete-modal').off('hidden.bs.modal');
                // Reload the inventory manage page and show that the group has been removed
                $state.go('.', null, {reload: true});
            });

            switch($scope.deleteOption){
                case 'promote':
                    GroupManageService.promote($scope.toDelete.id, $stateParams.inventory_id)
                        .then(() => {
                            if (parseInt($state.params.group_id) === $scope.toDelete.id) {
                                $state.go("^", null, {reload: true});
                            } else {
                                $state.go($state.current, null, {reload: true});
                            }
                            $('#group-delete-modal').modal('hide');
                            $('body').removeClass('modal-open');
                            $('.modal-backdrop').remove();
                        });
                    break;
                default:
                    GroupManageService.delete($scope.toDelete.id).then(() => {
                        if (parseInt($state.params.group_id) === $scope.toDelete.id) {
                            $state.go("^", null, {reload: true});
                        } else {
                            $state.go($state.current, null, {reload: true});
                        }
                        $('#group-delete-modal').modal('hide');
                        $('body').removeClass('modal-open');
                        $('.modal-backdrop').remove();
                    });
            }
        };
        $scope.updateGroup = function(group) {
            GroupManageService.getInventorySource({group: group.id}).then(res =>InventoryUpdate({
                scope: $scope,
                group_id: group.id,
                url: res.data.results[0].related.update,
                group_name: group.name,
                group_source: res.data.results[0].source
            }));
        };

        $scope.cancelUpdate = function (id) {
            CancelSourceUpdate({ scope: $scope, id: id });
        };

        // $scope.$parent governed by InventoryManageController, for unified multiSelect options
        $scope.$on('multiSelectList.selectionChanged', (event, selection) => {
            $scope.$parent.groupsSelected = selection.length > 0 ? true : false;
            $scope.$parent.groupsSelectedItems = selection.selectedItems;
        });

        $scope.copyMoveGroup = function(){
            // TODO: implement
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
