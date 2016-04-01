function copyGroupsDirectiveController($compile, $state, $scope, $location, Rest, ProcessErrors, CreateDialog,
    GetBasePath, Wait, GenerateList, GroupList, SearchInit, PaginateInit, GetRootGroups, ParamPass, Store) {
    var vm = this;
    var name;

    var params = ParamPass.get();

    if (params !== undefined) {
        var group_id = $state.params.group_id,
            parent_scope = params.scope,
            scope = parent_scope.$new(),
            parent_group = parent_scope.selected_group_id,
            url, group;
    } else {
        var group_id = $state.params.group_id;
        var parent_scope = $scope.$new();
        var scope = parent_scope.$new();
    }

    var inventory_id = $state.params.inventory_id;
    var PreviousSearchParams = Store('group_current_search_params');

    if (scope.removeGroupsCopyPostRefresh) {
        scope.removeGroupsCopyPostRefresh();
    }

    scope.removeGroupCopyPostRefresh = scope.$on('PostRefresh', function() {
        scope.copy_groups.forEach(function(row, i) {
            scope.copy_groups[i].checked = '0';
        });
        Wait('stop');

        // prevent backspace from navigation when not in input or textarea field
        $(document).on('keydown', function(e) {
            if (e.which === 8 && !$(e.target).is('input[type="text"], textarea')) {
                e.preventDefault();
            }
        });

    });

    if (scope.removeCopyDialogReady) {
        scope.removeCopyDialogReady();
    }

    scope.removeCopyDialogReady = scope.$on('CopyDialogReady', function() {
        var url = GetBasePath('inventory') + inventory_id + '/groups/';
        url += (parent_group) ? '?not__id__in=' + group_id + ',' + parent_group : '?not__id=' + group_id;
        GenerateList.inject(GroupList, {
            mode: 'lookup',
            id: 'copyMove-directive--copyGroupSelect',
            scope: scope
        });
        SearchInit({
            scope: scope,
            set: GroupList.name,
            list: GroupList,
            url: url
        });
        PaginateInit({
            scope: scope,
            list: GroupList,
            url: url,
            mode: 'lookup'
        });
        scope.search(GroupList.iterator);
    });

    if (scope.removeShowDialog) {
        scope.removeShowDialog();
    }

    scope.removeShowDialog = scope.$on('ShowDialog', function() {
        var d;
        scope.name = group.name;
        scope.copy_choice = "copy";
        d = angular.element(document.getElementById('copyMove-directive--copyGroupSelect'));
        $compile(d)(scope);
        scope.$emit('CopyDialogReady');
    });

    if (scope.removeRootGroupsReady) {
        scope.removeRootGroupsReady();
    }

    scope.removeRootGroupsReady = scope.$on('RootGroupsReady', function(e, root_groups) {
        scope.offer_root_group = true;
        scope.use_root_group = false;
        root_groups.every(function(row) {
            if (row.id === group_id) {
                scope.offer_root_group = false;
                return false;
            }
            return true;
        });
        url = GetBasePath('groups') + group_id + '/';
        Rest.setUrl(url);
        Rest.get()
            .success(function(data) {
                group = data;
                vm.name = group.name;
                scope.$emit('ShowDialog');
            })
            .error(function(data, status) {
                ProcessErrors(scope, data, status, null, {
                    hdr: 'Error!',
                    msg: 'Call to ' + url + ' failed. GET returned: ' + status
                });
            });
    });

    Wait('start');

    GetRootGroups({
        scope: scope,
        group_id: group_id,
        inventory_id: $state.params.inventory_id,
        callback: 'RootGroupsReady'
    });

    var restoreSearch = function() {
        // Restore search params and related stuff, plus refresh
        // groups and hosts lists
        SearchInit({
            scope: $scope,
            set: PreviousSearchParams.set,
            list: PreviousSearchParams.list,
            url: PreviousSearchParams.defaultUrl,
            iterator: PreviousSearchParams.iterator,
            sort_order: PreviousSearchParams.sort_order,
            setWidgets: false
        });
        $scope.refreshHostsOnGroupRefresh = true;
        //$scope.search(InventoryGroups.iterator, null, true, false, true);
    }

    var cancel = function() {
        restoreSearch(); // Restore all parent search stuff and refresh hosts and groups lists
        scope.$destroy();
        $state.go('inventoryManage', {}, {
            reload: true
        });
    };

    var allowSave = false;
    scope['toggle_' + GroupList.iterator] = function(id) {
        var count = 0,
            list = GroupList;
        scope[list.name].forEach(function(row, i) {
            if (row.id === id) {
                if (row.checked) {
                    scope[list.name][i].success_class = 'success';
                } else {
                    scope[list.name][i].success_class = '';
                }
            } else {
                scope[list.name][i].checked = 0;
                scope[list.name][i].success_class = '';
            }
        });
        // Check if any rows are checked
        scope[list.name].forEach(function(row) {
            if (row.checked) {
                count++;
            }
        });
        if (count === 0) {
            vm.allowSave = false;
        } else {
            vm.allowSave = true;
        }
    };

    scope.toggleUseRootGroup = function() {
        var list = GroupList;
        if (scope.use_root_group) {
            $('#group-copy-ok-button').removeAttr('disabled');
        } else {
            // check for group selection
            $('#group-copy-ok-button').attr('disabled', 'disabled');
            scope[list.name].every(function(row) {
                if (row.checked === 1) {
                    $('#group-copy-ok-button').removeAttr('disabled');
                    return false;
                }
                return true;
            });
        }
    };

    var performCopy = function() {
        var list = GroupList,
            target,
            url;

        Wait('start');

        if (scope.use_root_group) {
            target = null;
        } else {
            scope[list.name].every(function(row) {
                if (row.checked === 1) {
                    target = row;
                    return false;
                }
                return true;
            });
        }

        if (vm.copy_choice === 'move') {
            // Respond to move

            // disassociate the group from the original parent
            if (scope.removeGroupRemove) {
                scope.removeGroupRemove();
            }
            scope.removeGroupRemove = scope.$on('RemoveGroup', function() {
                if (parent_group > 0) {
                    // Only remove a group from a parent when the parent is a group and not the inventory root
                    url = GetBasePath('groups') + parent_group + '/children/';
                    Rest.setUrl(url);
                    Rest.post({
                            id: group.id,
                            disassociate: 1
                        })
                        .success(function() {
                            vm.cancel();
                        })
                        .error(function(data, status) {
                            ProcessErrors(scope, data, status, null, {
                                hdr: 'Error!',
                                msg: 'Failed to remove ' + group.name + ' from group ' + parent_group + '. POST returned: ' + status
                            });
                        });
                } else {
                    vm.cancel();
                }
            });

            // add the new group to the target
            url = (target) ?
                GetBasePath('groups') + target.id + '/children/' :
                GetBasePath('inventory') + inventory_id + '/groups/';
            group = {
                id: group.id,
                name: group.name,
                description: group.description,
                inventory: inventory_id
            };
            Rest.setUrl(url);
            Rest.post(group)
                .success(function() {
                    scope.$emit('RemoveGroup');
                })
                .error(function(data, status) {
                    var target_name = (target) ? target.name : 'inventory';
                    ProcessErrors(scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to add ' + group.name + ' to ' + target_name + '. POST returned: ' + status
                    });
                });
        } else {
            // Respond to copy by adding the new group to the target
            url = (target) ?
                GetBasePath('groups') + target.id + '/children/' :
                GetBasePath('inventory') + inventory_id + '/groups/';

            group = {
                id: group.id,
                name: group.name,
                description: group.description,
                inventory: inventory_id
            };

            Rest.setUrl(url);
            Rest.post(group)
                .success(function() {
                    vm.cancel();
                })
                .error(function(data, status) {
                    var target_name = (target) ? target.name : 'inventory';
                    ProcessErrors(scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to add ' + group.name + ' to ' + target_name + '. POST returned: ' + status
                    });
                });
        }
    };

    var copy_choice = 'copy';

    angular.extend(vm, {
        cancel: cancel,
        performCopy: performCopy,
        copy_choice: copy_choice,
        name: name,
        allowSave: allowSave
    });
};

export default ['$compile', '$state', '$scope', '$location', 'Rest', 'ProcessErrors', 'CreateDialog', 'GetBasePath', 'Wait', 'generateList', 'GroupList', 'SearchInit',
    'PaginateInit', 'GetRootGroups', 'ParamPass', 'Store', copyGroupsDirectiveController
];
