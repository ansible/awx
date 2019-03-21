/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 export default
    ['$scope', '$state', '$stateParams', 'listDefinition', 'InventoryUpdate',
    'GroupsService', 'CancelSourceUpdate',
    'GetHostsStatusMsg', 'Dataset', 'inventoryData', 'canAdd',
    'InventoryHostsStrings', '$transitions',
    function($scope, $state, $stateParams, listDefinition, InventoryUpdate,
        GroupsService, CancelSourceUpdate,
        GetHostsStatusMsg, Dataset, inventoryData, canAdd,
        InventoryHostsStrings, $transitions){

        let list = listDefinition;

        init();

        function init(){
            $scope.inventory_id = $stateParams.inventory_id;
            $scope.canAdhoc = inventoryData.summary_fields.user_capabilities.adhoc;
            $scope.canAdd = canAdd;

            $scope.strings = {
                deleteModal: {}
            };

            // Search init
            $scope.list = list;
            $scope[`${list.iterator}_dataset`] = Dataset.data;
            $scope[list.name] = $scope[`${list.iterator}_dataset`].results;

            if($state.current.name === "inventories.edit.groups") {
                $scope.rowBeingEdited = $state.params.group_id;
                $scope.listBeingEdited = "groups";
            }

            $scope.inventory_id = $stateParams.inventory_id;

            $scope.$watchCollection(list.name, function(){
                _.forEach($scope[list.name], processRow);
            });

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

        function processRow(group){
            if (group === undefined || group === null) {
                group = {};
            }

            angular.forEach($scope.groupsSelected, function(selectedGroup){
                if(selectedGroup.id === group.id) {
                    group.isSelected = true;
                }
            });

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
            if ($state.includes('inventories.edit.groups')) {
                $state.go('inventories.edit.groups.add');
            } else if ($state.includes('inventories.edit.rootGroups')) {
                $state.go('inventories.edit.rootGroups.add');
            }
        };
        $scope.editGroup = function(id){
            if ($state.includes('inventories.edit.groups')) {
                $state.go('inventories.edit.groups.edit', {group_id: id});
            } else if ($state.includes('inventories.edit.rootGroups')) {
                $state.go('inventories.edit.rootGroups.edit', {group_id: id});
            }
        };
        $scope.goToGroupGroups = function(id){
            $state.go('inventories.edit.groups.edit.nested_groups', {group_id: id});
        };
        $scope.deleteGroup = function(group){
            $scope.toDelete = {};
            $scope.strings.deleteModal = {};
            angular.extend($scope.toDelete, group);
            if($scope.toDelete.total_groups === 0 && $scope.toDelete.total_hosts === 0) {
                // This group doesn't have any child groups or hosts - the user is just trying to delete
                // the group
                $scope.deleteOption = "delete";
            }
            else {
                $scope.strings.deleteModal.group = InventoryHostsStrings.get('deletegroup.GROUP', $scope.toDelete.total_groups);
                $scope.strings.deleteModal.host = InventoryHostsStrings.get('deletegroup.HOST', $scope.toDelete.total_hosts);

                if($scope.toDelete.total_groups === 0 || $scope.toDelete.total_hosts === 0) {
                    if($scope.toDelete.total_groups === 0) {
                        $scope.strings.deleteModal.deleteGroupsHosts = InventoryHostsStrings.get('deletegroup.DELETE_HOST', $scope.toDelete.total_hosts);
                        $scope.strings.deleteModal.promoteGroupsHosts = InventoryHostsStrings.get('deletegroup.PROMOTE_HOST', $scope.toDelete.total_hosts);
                    }
                    else if($scope.toDelete.total_hosts === 0) {
                        $scope.strings.deleteModal.deleteGroupsHosts = InventoryHostsStrings.get('deletegroup.DELETE_GROUP', $scope.toDelete.total_groups);
                        $scope.strings.deleteModal.promoteGroupsHosts = InventoryHostsStrings.get('deletegroup.PROMOTE_GROUP', $scope.toDelete.total_groups);
                    }
                }
                else {
                    $scope.strings.deleteModal.deleteGroupsHosts = InventoryHostsStrings.get('deletegroup.DELETE_GROUPS_AND_HOSTS', {groups: $scope.toDelete.total_groups, hosts: $scope.toDelete.total_hosts});
                    $scope.strings.deleteModal.promoteGroupsHosts = InventoryHostsStrings.get('deletegroup.PROMOTE_GROUPS_AND_HOSTS', {groups: $scope.toDelete.total_groups, hosts: $scope.toDelete.total_hosts});
                }
            }

            $('#group-delete-modal').modal('show');
        };
        $scope.confirmDelete = function(){
            let reloadListStateParams = null;

            if($scope.groups.length === 1 && $state.params.group_search && _.has($state, 'params.group_search.page') && $state.params.group_search.page !== '1') {
                reloadListStateParams = _.cloneDeep($state.params);
                reloadListStateParams.group_search.page = (parseInt(reloadListStateParams.group_search.page)-1).toString();
            }

            switch($scope.deleteOption){
                case 'promote':
                    GroupsService.promote($scope.toDelete.id, $stateParams.inventory_id)
                        .then(() => {
                            if (parseInt($state.params.group_id) === $scope.toDelete.id) {
                                $state.go("^", reloadListStateParams, {reload: true});
                            } else {
                                $state.go($state.current, reloadListStateParams, {reload: true});
                            }
                            setTimeout(function(){
                                $('#group-delete-modal').modal('hide');
                                $('body').removeClass('modal-open');
                                $('.modal-backdrop').remove();
                            }, 1000);
                        });
                    break;
                default:
                    GroupsService.delete($scope.toDelete.id).then(() => {
                        if (parseInt($state.params.group_id) === $scope.toDelete.id) {
                            $state.go("^", reloadListStateParams, {reload: true});
                        } else {
                            $state.go($state.current, reloadListStateParams, {reload: true});
                        }
                        setTimeout(function(){
                            $('#group-delete-modal').modal('hide');
                            $('body').removeClass('modal-open');
                            $('.modal-backdrop').remove();
                        }, 1000);
                    });
            }
        };
        $scope.updateGroup = function(group) {
            GroupsService.getInventorySource({group: group.id}).then(res =>InventoryUpdate({
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

        var cleanUpStateChangeListener = $transitions.onSuccess({}, function(trans) {
             if (trans.to().name === "inventories.edit.groups.edit") {
                 $scope.rowBeingEdited = trans.params('to').group_id;
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

            $state.go('inventories.edit.adhoc', {pattern: pattern});
        };

    }];
