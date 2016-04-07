function CopyHostsCtrl($compile, $state, $scope, Rest, ProcessErrors, CreateDialog, GetBasePath, Wait, GenerateList, GroupList, SearchInit, PaginateInit, ParamPass, Store) {
    var vm = this;
    var name;

    var host_id = $state.params.host_id;
    var inventory_id = $state.params.inventory_id;
    var url, host;

    var params = ParamPass.get();
    if (params !== undefined) {
        var group_scope = params.group_scope,
            parent_scope = params.host_scope,
            parent_group = group_scope.selected_group_id,
            scope = parent_scope.$new();
    } else {
        var group_scope = $scope.$new();
        var parent_scope = $scope.$new();
        var scope = parent_scope.$new();
    }

    var PreviousSearchParams = Store('group_current_search_params');

    if (scope.removeHostCopyPostRefresh) {
        scope.removeHostCopyPostRefresh();
    }
    scope.removeHostCopyPostRefresh = scope.$on('PostRefresh', function() {
        scope.copy_groups.forEach(function(row, i) {
            scope.copy_groups[i].checked = '0';
        });
        Wait('stop');
        // prevent backspace from navigation when not in input or textarea field
        $(document).on("keydown", function(e) {
            if (e.which === 8 && !$(e.target).is('input[type="text"], textarea')) {
                e.preventDefault();
            }
        });
    });

    if (scope.removeHostCopyDialogReady) {
        scope.removeHostCopyDialogReady();
    }
    scope.removeCopyDialogReady = scope.$on('HostCopyDialogReady', function() {
        var url = GetBasePath('inventory') + inventory_id + '/groups/';
        GenerateList.inject(GroupList, {
            mode: 'lookup',
            id: 'copyMove-directive--copyHostSelect',
            scope: scope
                //,
                //instructions: instructions
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
        scope.search(GroupList.iterator, null, true, false);
    });

    if (scope.removeShowDialog) {
        scope.removeShowDialog();
    }
    scope.removeShowDialog = scope.$on('ShowDialog', function() {
        var d;
        scope.name = host.name;
        d = angular.element(document.getElementById('copyMove-directive--copyHostPanel'));
        $compile(d)(scope);
        scope.$emit('HostCopyDialogReady');
    });

    Wait('start');

    url = GetBasePath('hosts') + host_id + '/';
    Rest.setUrl(url);
    Rest.get()
        .success(function(data) {
            host = data;
            vm.name = host.name;
            scope.$emit('ShowDialog');
        })
        .error(function(data, status) {
            ProcessErrors(scope, data, status, null, {
                hdr: 'Error!',
                msg: 'Call to ' + url + ' failed. GET returned: ' + status
            });
        });

    var cancel = function() {
        $(document).off("keydown");
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
            // disassociate the host from the original parent
            if (scope.removeHostRemove) {
                scope.removeHostRemove();
            }
            scope.removeHostRemove = scope.$on('RemoveHost', function() {
                if (parent_group > 0) {
                    // Only remove a host from a parent when the parent is a group and not the inventory root
                    url = GetBasePath('groups') + parent_group + '/hosts/';
                    Rest.setUrl(url);
                    Rest.post({
                            id: host.id,
                            disassociate: 1
                        })
                        .success(function() {
                            vm.cancel();
                        })
                        .error(function(data, status) {
                            ProcessErrors(scope, data, status, null, {
                                hdr: 'Error!',
                                msg: 'Failed to remove ' + host.name + ' from group ' + parent_group + '. POST returned: ' + status
                            });
                        });
                } else {
                    vm.cancel();
                }
            });

            // add the new host to the target
            url = GetBasePath('groups') + target.id + '/hosts/';
            Rest.setUrl(url);
            Rest.post(host)
                .success(function() {
                    scope.$emit('RemoveHost');
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to add ' + host.name + ' to ' + target.name + '. POST returned: ' + status
                    });
                });
        } else {
            // Respond to copy by adding the new host to the target
            url = GetBasePath('groups') + target.id + '/hosts/';
            Rest.setUrl(url);
            Rest.post(host)
                .success(function() {
                    vm.cancel();
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to add ' + host.name + ' to ' + target.name + '. POST returned: ' + status
                    });
                });
        }
    };


    var copy_choice = 'copy';

    angular.extend(vm, {
        copy_choice: copy_choice,
        name: name,
        cancel: cancel,
        allowSave: allowSave,
        performCopy: performCopy
    });
}

export default ['$compile', '$state', '$scope', 'Rest', 'ProcessErrors', 'CreateDialog', 'GetBasePath', 'Wait', 'generateList', 'GroupList', 'SearchInit',
    'PaginateInit', 'ParamPass', 'Store', CopyHostsCtrl
];
