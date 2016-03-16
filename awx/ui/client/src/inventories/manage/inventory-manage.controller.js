/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Inventories
 * @description This controller's for the Inventory page
 */

function InventoriesManage($log, $scope, $rootScope, $location,
    $state, $compile, generateList, ClearScope, Empty, Wait, Rest, Alert,
    GetBasePath, ProcessErrors, InventoryGroups,
    InjectHosts, Find, HostsReload, SearchInit, PaginateInit, GetSyncStatusMsg,
    GetHostsStatusMsg, GroupsEdit, InventoryUpdate, GroupsCancelUpdate,
    ViewUpdateStatus, GroupsDelete, Store, HostsEdit, HostsDelete,
    EditInventoryProperties, ToggleHostEnabled, ShowJobSummary,
    InventoryGroupsHelp, HelpDialog,
    GroupsCopy, HostsCopy, $stateParams) {

    var PreviousSearchParams,
        url,
        hostScope = $scope.$new();

    ClearScope();

    // TODO: only display adhoc button if the user has permission to use it.
    // TODO: figure out how to get the action-list partial to update so that
    // the tooltip can be changed based off things being selected or not.
    $scope.adhocButtonTipContents = "Launch adhoc command for the inventory";

    // watcher for the group list checkbox changes
    $scope.$on('multiSelectList.selectionChanged', function(e, selection) {
        if (selection.length > 0) {
            $scope.groupsSelected = true;
            // $scope.adhocButtonTipContents = "Launch adhoc command for the "
            //     + "selected groups and hosts.";
        } else {
            $scope.groupsSelected = false;
            // $scope.adhocButtonTipContents = "Launch adhoc command for the "
            //     + "inventory.";
        }
        $scope.groupsSelectedItems = selection.selectedItems;
    });

    // watcher for the host list checkbox changes
    hostScope.$on('multiSelectList.selectionChanged', function(e, selection) {
        // you need this so that the event doesn't bubble to the watcher above
        // for the host list
        e.stopPropagation();
        if (selection.length === 0) {
            $scope.hostsSelected = false;
        } else if (selection.length === 1) {
            $scope.systemTrackingTooltip = "Compare host over time";
            $scope.hostsSelected = true;
            $scope.systemTrackingDisabled = false;
        } else if (selection.length === 2) {
            $scope.systemTrackingTooltip = "Compare hosts against each other";
            $scope.hostsSelected = true;
            $scope.systemTrackingDisabled = false;
        } else {
            $scope.hostsSelected = true;
            $scope.systemTrackingDisabled = true;
        }
        $scope.hostsSelectedItems = selection.selectedItems;
    });

    $scope.systemTracking = function() {
        var hostIds =  _.map($scope.hostsSelectedItems, function(x){
            return x.id;
        });
        $state.transitionTo('systemTracking',
                     {  inventory: $scope.inventory,
                        inventoryId: $scope.inventory.id,
                        hosts: $scope.hostsSelectedItems,
                        hostIds: hostIds
                     });
    };

    // populates host patterns based on selected hosts/groups
    $scope.populateAdhocForm = function() {
        var host_patterns = "all";
        if ($scope.hostsSelected || $scope.groupsSelected) {
            var allSelectedItems = [];
            if ($scope.groupsSelectedItems) {
                allSelectedItems = allSelectedItems.concat($scope.groupsSelectedItems);
            }
            if ($scope.hostsSelectedItems) {
                allSelectedItems = allSelectedItems.concat($scope.hostsSelectedItems);
            }
            if (allSelectedItems) {
                host_patterns = _.pluck(allSelectedItems, "name").join(":");
            }
        }
        $rootScope.hostPatterns = host_patterns;
        $state.go('inventoryManage.adhoc');
    };

    $scope.refreshHostsOnGroupRefresh = false;
    $scope.selected_group_id = null;

    Wait('start');


    if ($scope.removeHostReloadComplete) {
        $scope.removeHostReloadComplete();
    }
    $scope.removeHostReloadComplete = $scope.$on('HostReloadComplete', function() {
        if ($scope.initial_height) {
            var host_height = $('#hosts-container .well').height(),
                group_height = $('#group-list-container .well').height(),
                new_height;

            if (host_height > group_height) {
                new_height = host_height - (host_height - group_height);
            }
            else if (host_height < group_height) {
                new_height = host_height + (group_height - host_height);
            }
            if (new_height) {
                $('#hosts-container .well').height(new_height);
            }
            $scope.initial_height = null;
        }
    });

    if ($scope.removeRowCountReady) {
        $scope.removeRowCountReady();
    }
    $scope.removeRowCountReady = $scope.$on('RowCountReady', function(e, rows) {
        // Add hosts view
        $scope.show_failures = false;
        InjectHosts({
            group_scope: $scope,
            host_scope: hostScope,
            inventory_id: $scope.inventory.id,
            tree_id: null,
            group_id: null,
            pageSize: rows
        });

        SearchInit({ scope: $scope, set: 'groups', list: InventoryGroups, url: $scope.inventory.related.root_groups });
        PaginateInit({ scope: $scope, list: InventoryGroups , url: $scope.inventory.related.root_groups, pageSize: rows });
        $scope.search(InventoryGroups.iterator, null, true);
    });

    if ($scope.removeInventoryLoaded) {
        $scope.removeInventoryLoaded();
    }
    $scope.removeInventoryLoaded = $scope.$on('InventoryLoaded', function() {
        var rows;

        // Add groups view
        generateList.inject(InventoryGroups, {
            mode: 'edit',
            id: 'group-list-container',
            searchSize: 'col-lg-6 col-md-6 col-sm-6 col-xs-12',
            scope: $scope
        });

        rows = 20;
        hostScope.host_page_size = rows;
        $scope.group_page_size = rows;

        $scope.show_failures = false;
        InjectHosts({
            group_scope: $scope,
            host_scope: hostScope,
            inventory_id: $scope.inventory.id,
            tree_id: null,
            group_id: null,
            pageSize: rows
        });

        // Load data
        SearchInit({
            scope: $scope,
            set: 'groups',
            list: InventoryGroups,
            url: $scope.inventory.related.root_groups
        });

        PaginateInit({
            scope: $scope,
            list: InventoryGroups ,
            url: $scope.inventory.related.root_groups,
            pageSize: rows
        });

        $scope.search(InventoryGroups.iterator, null, true);

        $scope.$emit('WatchUpdateStatus');  // init socket io conneciton and start watching for status updates
    });

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function(e, set) {
        if (set === 'groups') {
            $scope.groups.forEach( function(group, idx) {
                var stat, hosts_status;
                stat = GetSyncStatusMsg({
                    status: group.summary_fields.inventory_source.status,
                    has_inventory_sources: group.has_inventory_sources,
                    source: ( (group.summary_fields.inventory_source) ? group.summary_fields.inventory_source.source : null )
                }); // from helpers/Groups.js
                $scope.groups[idx].status_class = stat['class'];
                $scope.groups[idx].status_tooltip = stat.tooltip;
                $scope.groups[idx].launch_tooltip = stat.launch_tip;
                $scope.groups[idx].launch_class = stat.launch_class;
                hosts_status = GetHostsStatusMsg({
                    active_failures: group.hosts_with_active_failures,
                    total_hosts: group.total_hosts,
                    inventory_id: $scope.inventory.id,
                    group_id: group.id
                }); // from helpers/Groups.js
                $scope.groups[idx].hosts_status_tip = hosts_status.tooltip;
                $scope.groups[idx].show_failures = hosts_status.failures;
                $scope.groups[idx].hosts_status_class = hosts_status['class'];

                $scope.groups[idx].source = (group.summary_fields.inventory_source) ? group.summary_fields.inventory_source.source : null;
                $scope.groups[idx].status = (group.summary_fields.inventory_source) ? group.summary_fields.inventory_source.status : null;

            });
            if ($scope.refreshHostsOnGroupRefresh) {
                $scope.refreshHostsOnGroupRefresh = false;
                HostsReload({
                    scope: hostScope,
                    group_id: $scope.selected_group_id,
                    inventory_id: $scope.inventory.id,
                    pageSize: hostScope.host_page_size
                });
            }
            else {
                Wait('stop');
            }
        }
    });

    // Load Inventory
    url = GetBasePath('inventory') + $stateParams.inventory_id + '/';
    Rest.setUrl(url);
    Rest.get()
        .success(function (data) {
            $scope.inventory = data;
            $scope.$emit('InventoryLoaded');
        })
        .error(function (data, status) {
            ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve inventory: ' + $stateParams.inventory_id +
                ' GET returned status: ' + status });
        });

    // start watching for real-time updates
    if ($rootScope.removeWatchUpdateStatus) {
        $rootScope.removeWatchUpdateStatus();
    }
    $rootScope.removeWatchUpdateStatus = $rootScope.$on('JobStatusChange-inventory', function(e, data) {
        var stat, group;
        if (data.group_id) {
            group = Find({ list: $scope.groups, key: 'id', val: data.group_id });
            if (data.status === "failed" || data.status === "successful") {
                if (data.group_id === $scope.selected_group_id || group) {
                    // job completed, fefresh all groups
                    $log.debug('Update completed. Refreshing the tree.');
                    $scope.refreshGroups();
                }
            }
            else if (group) {
                // incremental update, just update
                $log.debug('Status of group: ' + data.group_id + ' changed to: ' + data.status);
                stat = GetSyncStatusMsg({
                    status: data.status,
                    has_inventory_sources: group.has_inventory_sources,
                    source: group.source
                });
                $log.debug('changing tooltip to: ' + stat.tooltip);
                group.status = data.status;
                group.status_class = stat['class'];
                group.status_tooltip = stat.tooltip;
                group.launch_tooltip = stat.launch_tip;
                group.launch_class = stat.launch_class;
            }
        }
    });

    // Load group on selection
    function loadGroups(url) {
        SearchInit({ scope: $scope, set: 'groups', list: InventoryGroups, url: url });
        PaginateInit({ scope: $scope, list: InventoryGroups , url: url, pageSize: $scope.group_page_size });
        $scope.search(InventoryGroups.iterator, null, true, false, true);
    }

    $scope.refreshHosts = function() {
        HostsReload({
            scope: hostScope,
            group_id: $scope.selected_group_id,
            inventory_id: $scope.inventory.id,
            pageSize: hostScope.host_page_size
        });
    };

    $scope.refreshGroups = function() {
        $scope.refreshHostsOnGroupRefresh = true;
        $scope.search(InventoryGroups.iterator, null, true, false, true);
    };

    $scope.restoreSearch = function() {
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
        $scope.search(InventoryGroups.iterator, null, true, false, true);
    };

    $scope.groupSelect = function(id) {
        var groups = [], group = Find({ list: $scope.groups, key: 'id', val: id });
        if($state.params.groups){
            groups.push($state.params.groups);
        }
        groups.push(group.id);
        groups = groups.join();
        $state.transitionTo('inventoryManage', {inventory_id: $state.params.inventory_id, groups: groups}, { notify: false });
        loadGroups(group.related.children, group.id);
    };

    $scope.createGroup = function () {
        PreviousSearchParams = Store('group_current_search_params');
        GroupsEdit({
            scope: $scope,
            inventory_id: $scope.inventory.id,
            group_id: $scope.selected_group_id,
            mode: 'add'
        });
    };

    $scope.editGroup = function (id) {
        PreviousSearchParams = Store('group_current_search_params');
        GroupsEdit({
            scope: $scope,
            inventory_id: $scope.inventory.id,
            group_id: id,
            mode: 'edit'
        });
    };

    // Launch inventory sync
    $scope.updateGroup = function (id) {
        var group = Find({ list: $scope.groups, key: 'id', val: id });
        if (group) {
            if (Empty(group.source)) {
                // if no source, do nothing.
            } else if (group.status === 'updating') {
                Alert('Update in Progress', 'The inventory update process is currently running for group <em>' +
                    group.name + '</em> Click the <i class="fa fa-refresh"></i> button to monitor the status.', 'alert-info', null, null, null, null, true);
            } else {
                Wait('start');
                Rest.setUrl(group.related.inventory_source);
                Rest.get()
                    .success(function (data) {
                        InventoryUpdate({
                            scope: $scope,
                            url: data.related.update,
                            group_name: data.summary_fields.group.name,
                            group_source: data.source,
                            group_id: group.id,
                        });
                    })
                    .error(function (data, status) {
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve inventory source: ' +
                            group.related.inventory_source + ' GET returned status: ' + status });
                    });
            }
        }
    };

    $scope.cancelUpdate = function (id) {
        GroupsCancelUpdate({ scope: $scope, id: id });
    };

    $scope.viewUpdateStatus = function (id) {
        ViewUpdateStatus({
            scope: $scope,
            group_id: id
        });
    };

    $scope.copyGroup = function(id) {
        PreviousSearchParams = Store('group_current_search_params');
        GroupsCopy({
            scope: $scope,
            group_id: id
        });
    };

    $scope.deleteGroup = function (id) {
        GroupsDelete({
            scope: $scope,
            group_id: id,
            inventory_id: $scope.inventory.id
        });
    };

    $scope.editInventoryProperties = function () {
        // EditInventoryProperties({ scope: $scope, inventory_id: $scope.inventory.id });
        $location.path('/inventories/' + $scope.inventory.id + '/');
    };

    hostScope.createHost = function () {
        HostsEdit({
            host_scope: hostScope,
            group_scope: $scope,
            mode: 'add',
            host_id: null,
            selected_group_id: $scope.selected_group_id,
            inventory_id: $scope.inventory.id
        });
    };

    hostScope.editHost = function (host_id) {
        HostsEdit({
            host_scope: hostScope,
            group_scope: $scope,
            mode: 'edit',
            host_id: host_id,
            inventory_id: $scope.inventory.id
        });
    };

    hostScope.deleteHost = function (host_id, host_name) {
        HostsDelete({
            parent_scope: $scope,
            host_scope: hostScope,
            host_id: host_id,
            host_name: host_name
        });
    };

    hostScope.copyHost = function(id) {
        PreviousSearchParams = Store('group_current_search_params');
        HostsCopy({
            group_scope: $scope,
            host_scope: hostScope,
            host_id: id
        });
    };

    /*hostScope.restoreSearch = function() {
        SearchInit({
            scope: hostScope,
            set: PreviousSearchParams.set,
            list: PreviousSearchParams.list,
            url: PreviousSearchParams.defaultUrl,
            iterator: PreviousSearchParams.iterator,
            sort_order: PreviousSearchParams.sort_order,
            setWidgets: false
        });
        hostScope.search('host');
    };*/

    hostScope.toggleHostEnabled = function (host_id, external_source) {
        ToggleHostEnabled({
            parent_scope: $scope,
            host_scope: hostScope,
            host_id: host_id,
            external_source: external_source
        });
    };

    hostScope.showJobSummary = function (job_id) {
        ShowJobSummary({
            job_id: job_id
        });
    };

    $scope.showGroupHelp = function (params) {
        var opts = {
            defn: InventoryGroupsHelp
        };
        if (params) {
            opts.autoShow = params.autoShow || false;
        }
        HelpDialog(opts);
    }
;
    $scope.showHosts = function (group_id, show_failures) {
        // Clicked on group
        if (group_id !== null) {
            Wait('start');
            hostScope.show_failures = show_failures;
            $scope.groupSelect(group_id);
            hostScope.hosts = [];
            $scope.show_failures = show_failures; // turn on failed hosts
            // filter in hosts view
        } else {
            Wait('stop');
        }
    };

    if ($scope.removeGroupDeleteCompleted) {
        $scope.removeGroupDeleteCompleted();
    }
    $scope.removeGroupDeleteCompleted = $scope.$on('GroupDeleteCompleted',
        function() {
            $scope.refreshGroups();
        }
    );
}

export default [
    '$log', '$scope', '$rootScope', '$location',
        '$state', '$compile', 'generateList', 'ClearScope', 'Empty', 'Wait',
        'Rest', 'Alert', 'GetBasePath', 'ProcessErrors',
        'InventoryGroups', 'InjectHosts', 'Find', 'HostsReload',
        'SearchInit', 'PaginateInit', 'GetSyncStatusMsg', 'GetHostsStatusMsg',
        'GroupsEdit', 'InventoryUpdate', 'GroupsCancelUpdate', 'ViewUpdateStatus',
        'GroupsDelete', 'Store', 'HostsEdit', 'HostsDelete',
        'EditInventoryProperties', 'ToggleHostEnabled', 'ShowJobSummary',
        'InventoryGroupsHelp', 'HelpDialog', 'GroupsCopy',
        'HostsCopy', '$stateParams', InventoriesManage,
];
