/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Inventories.js
 *
 *  Controller functions for the Inventory model.
 *
 */
 
'use strict';

function InventoriesList($scope, $rootScope, $location, $log, $routeParams, $compile, $filter, Rest, Alert, InventoryList, GenerateList,
    LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller, ClearScope, ProcessErrors, GetBasePath, Wait, Stream,
    EditInventoryProperties, Find, Empty, LogViewer) {
    
    //ClearScope();
  
    var list = InventoryList,
        defaultUrl = GetBasePath('inventory'),
        view = GenerateList,
        paths = $location.path().replace(/^\//, '').split('/'),
        mode = (paths[0] === 'inventories') ? 'edit' : 'select';

    function ellipsis(a) {
        if (a.length > 20) {
            return a.substr(0,20) + '...';
        }
        return a;
    }

    function attachElem(event, html, title) {
        var elem = $(event.target).parent();
        try {
            elem.tooltip('hide');
            elem.popover('destroy');
        }
        catch(err) {
            //ignore
        }
        elem.attr({ "aw-pop-over": html, "data-title": title, "data-placement": "right" });
        $compile(elem)($scope);
        elem.on('shown.bs.popover', function() {
            $('.popover').each(function() {
                $compile($(this))($scope);  //make nested directives work!
            });
            $('.popover-content, .popover-title').click(function() {
                elem.popover('hide');
            });
        });
        elem.popover('show');
    }

    view.inject(InventoryList, { mode: mode, scope: $scope });
    $rootScope.flashMessage = null;

    SearchInit({
        scope: $scope,
        set: 'inventories',
        list: list,
        url: defaultUrl
    });
    
    PaginateInit({
        scope: $scope,
        list: list,
        url: defaultUrl
    });

    if ($routeParams.name) {
        $scope[InventoryList.iterator + 'InputDisable'] = false;
        $scope[InventoryList.iterator + 'SearchValue'] = $routeParams.name;
        $scope[InventoryList.iterator + 'SearchField'] = 'name';
        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.name.label;
        $scope[InventoryList.iterator + 'SearchSelectValue'] = null;
    }

    if ($routeParams.has_active_failures) {
        $scope[InventoryList.iterator + 'InputDisable'] = true;
        $scope[InventoryList.iterator + 'SearchValue'] = $routeParams.has_active_failures;
        $scope[InventoryList.iterator + 'SearchField'] = 'has_active_failures';
        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.has_active_failures.label;
        $scope[InventoryList.iterator + 'SearchSelectValue'] = ($routeParams.has_active_failures === 'true') ? {
            value: 1
        } : {
            value: 0
        };
    }

    if ($routeParams.has_inventory_sources) {
        $scope[InventoryList.iterator + 'InputDisable'] = true;
        $scope[InventoryList.iterator + 'SearchValue'] = $routeParams.has_inventory_sources;
        $scope[InventoryList.iterator + 'SearchField'] = 'has_inventory_sources';
        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.has_inventory_sources.label;
        $scope[InventoryList.iterator + 'SearchSelectValue'] = ($routeParams.has_inventory_sources === 'true') ? {
            value: 1
        } : {
            value: 0
        };
    }

    if ($routeParams.inventory_sources_with_failures) {
        // pass a value of true, however this field actually contains an integer value
        $scope[InventoryList.iterator + 'InputDisable'] = true;
        $scope[InventoryList.iterator + 'SearchValue'] = $routeParams.inventory_sources_with_failures;
        $scope[InventoryList.iterator + 'SearchField'] = 'inventory_sources_with_failures';
        $scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields.inventory_sources_with_failures.label;
        $scope[InventoryList.iterator + 'SearchType'] = 'gtzero';
    }

    $scope.search(list.iterator);

    LoadBreadCrumbs();

    if ($scope.removePostRefresh) {
        $scope.removePostRefresh();
    }
    $scope.removePostRefresh = $scope.$on('PostRefresh', function () {
        //If we got here by deleting an inventory, stop the spinner and cleanup events
        Wait('stop');
        try {
            $('#prompt-modal').modal('hide');
        }
        catch(e) {
            // ignore
        }
        $scope.inventories.forEach(function(inventory, idx) {
            $scope.inventories[idx].launch_class = "";
            if (inventory.has_inventory_sources) {
                if (inventory.inventory_sources_with_failures > 0) {
                    $scope.inventories[idx].syncStatus = 'error';
                    $scope.inventories[idx].syncTip = inventory.groups_with_active_failures + ' groups with sync failures. Click for details';
                }
                else {
                    $scope.inventories[idx].syncStatus = 'successful';
                    $scope.inventories[idx].syncTip = 'No inventory sync failures. Click for details.';
                }
            }
            else {
                $scope.inventories[idx].syncStatus = 'na';
                $scope.inventories[idx].syncTip = 'Not configured for inventory sync.';
                $scope.inventories[idx].launch_class = "btn-disabled";
            }
            if (inventory.has_active_failures) {
                $scope.inventories[idx].hostsStatus = 'error';
                $scope.inventories[idx].hostsTip = inventory.hosts_with_active_failures + ' hosts with failures. Click for details.';
            }
            else if (inventory.total_hosts) {
                $scope.inventories[idx].hostsStatus = 'successful';
                $scope.inventories[idx].hostsTip = 'No hosts with failures. Click for details.';
            }
            else {
                $scope.inventories[idx].hostsStatus = 'none';
                $scope.inventories[idx].hostsTip = 'Inventory contains 0 hosts.';
            }
        });
    });

    if ($scope.removeRefreshInventories) {
        $scope.removeRefreshInventories();
    }
    $scope.removeRefreshInventories = $scope.$on('RefreshInventories', function () {
        // Reflect changes after inventory properties edit completes
        $scope.search(list.iterator);
    });

    if ($scope.removeHostSummaryReady) {
        $scope.removeHostSummaryReady();
    }
    $scope.removeHostSummaryReady = $scope.$on('HostSummaryReady', function(e, event, data) {
        
        var html, title = "Recent Jobs";
        Wait('stop');
        if (data.count > 0) {
            html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
            html += "<thead>\n";
            html += "<tr>";
            html += "<th>Status</th>";
            html += "<th>Finished</th>";
            html += "<th>View</th>";
            html += "<th>Name</th>";
            html += "</tr>\n";
            html += "</thead>\n";
            html += "<tbody>\n";
            
            data.results.forEach(function(row) {
                html += "<tr>\n";
                html += "<td><a ng-click=\"viewJob('" + row.url + "')\" " + "aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) +
                    ". Click for details\" aw-tip-placement=\"top\"><i class=\"fa icon-job-" +
                    row.status + "\"></i></a></td>\n";
                html += "<td>" + ($filter('date')(row.finished,'MM/dd HH:mm:ss')).replace(/ /,'<br />') + "</td>";
                html += "<td><a href=\"/#/jobs/" + row.id + "/job_events\">Events</a><br />" +
                    "<a href=\"/#/jobs/" + row.id + "/job_host_summaries\">Hosts</a></td>";
                html += "<td><a href=\"\" ng-click=\"viewJob('" + row.url + "')\" >" + ellipsis(row.name) + "</a></td>";
                html += "</tr>\n";
            });
            html += "</tbody>\n";
            html += "</table>\n";
            html += "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";
        }
        else {
            html = "<p>No recent job data available for this inventory.</p>\n" +
                "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";
        }
        attachElem(event, html, title);
    });

    if ($scope.removeGroupSummaryReady) {
        $scope.removeGroupSummaryReady();
    }
    $scope.removeGroupSummaryReady = $scope.$on('GroupSummaryReady', function(e, event, inventory, data) {
        var html, title;
        
        Wait('stop');

        // Build the html for our popover
        html = "<table class=\"table table-condensed flyout\" style=\"width: 100%\">\n";
        html += "<thead>\n";
        html += "<tr>";
        html += "<th>Status</th>";
        html += "<th>Last Sync</th>";
        html += "<th>Group</th>";
        html += "</tr>";
        html += "</thead>\n";
        html += "<tbody>\n";
        data.results.forEach( function(row) {
            html += "<tr>";
            html += "<td><a href=\"\" ng-click=\"viewJob('" + row.related.last_update + "')\" aw-tool-tip=\"" + row.status.charAt(0).toUpperCase() + row.status.slice(1) + ". Click for details\" aw-tip-placement=\"top\"><i class=\"fa icon-job-" + row.status + "\"></i></a></td>";
            html += "<td>" + ($filter('date')(row.last_updated,'MM/dd HH:mm:ss')).replace(/ /,'<br />') + "</td>";
            html += "<td><a href=\"\" ng-click=\"viewJob('" + row.related.last_update + "')\">" + ellipsis(row.summary_fields.group.name) + "</a></td>";
            html += "</tr>\n";
        });
        html += "</tbody>\n";
        html += "</table>\n";
        html += "<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>\n";
        title = "Sync Status";
        attachElem(event, html, title);
    });

    $scope.showGroupSummary = function(event, id) {
        var inventory;
        if (!Empty(id)) {
            inventory = Find({ list: $scope.inventories, key: 'id', val: id });
            if (inventory.syncStatus !== 'na') {
                Wait('start');
                Rest.setUrl(inventory.related.inventory_sources + '?or__source=ec2&or__source=rax&order_by=-last_job_run&page_size=5');
                Rest.get()
                    .success(function(data) {
                        $scope.$emit('GroupSummaryReady', event, inventory, data);
                    })
                    .error(function(data, status) {
                        ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + inventory.related.inventory_sources + ' failed. GET returned status: ' + status
                        });
                    });
            }
        }
    };

    $scope.showHostSummary = function(event, id) {
        var url, inventory;
        if (!Empty(id)) {
            inventory = Find({ list: $scope.inventories, key: 'id', val: id });
            if (inventory.total_hosts > 0) {
                Wait('start');
                url = GetBasePath('jobs') + "?type=job&inventory=" + id + "&failed=";
                url += (inventory.has_active_failures) ? 'true' : "false";
                url += "&order_by=-finished&page_size=5";
                Rest.setUrl(url);
                Rest.get()
                    .success( function(data) {
                        $scope.$emit('HostSummaryReady', event, data);
                    })
                    .error( function(data, status) {
                        ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. GET returned: ' + status
                        });
                    });
            }
        }
    };

    $scope.viewJob = function(url) {
        LogViewer({
            scope: $scope,
            url: url
        });
    };

    $scope.showActivity = function () {
        Stream({ scope:  $scope });
    };

    $scope.editInventoryProperties = function (inventory_id) {
        EditInventoryProperties({ scope: $scope, inventory_id: inventory_id });
    };

    $scope.addInventory = function () {
        $location.path($location.path() + '/add');
    };

    $scope.editInventory = function (id) {
        $location.path($location.path() + '/' + id);
    };

    $scope.deleteInventory = function (id, name) {

        var action = function () {
            var url = defaultUrl + id + '/';
            $('#prompt-modal').on('hidden.bs.modal', function () {
                Wait('start');
            });
            $('#prompt-modal').modal('hide');
            Rest.setUrl(url);
            Rest.destroy()
                .success(function () {
                    $scope.search(list.iterator);
                })
                .error(function (data, status) {
                    ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status
                    });
                });
        };

        Prompt({
            hdr: 'Delete',
            body: '<div class=\"alert alert-info\">Delete inventory ' + name + '?</div>',
            action: action
        });
    };

    $scope.lookupOrganization = function (organization_id) {
        Rest.setUrl(GetBasePath('organizations') + organization_id + '/');
        Rest.get()
            .success(function (data) {
                return data.name;
            });
    };


    // Failed jobs link. Go to the jobs tabs, find all jobs for the inventory and sort by status
    $scope.viewJobs = function (id) {
        $location.url('/jobs/?inventory__int=' + id);
    };

    $scope.viewFailedJobs = function (id) {
        $location.url('/jobs/?inventory__int=' + id + '&status=failed');
    };
}

InventoriesList.$inject = ['$scope', '$rootScope', '$location', '$log', '$routeParams', '$compile', '$filter', 'Rest', 'Alert', 'InventoryList', 'GenerateList',
    'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
    'GetBasePath', 'Wait', 'Stream', 'EditInventoryProperties', 'Find', 'Empty', 'LogViewer'
];


function InventoriesAdd($scope, $rootScope, $compile, $location, $log, $routeParams, InventoryForm, GenerateForm, Rest,
    Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, GenerateList, OrganizationList, SearchInit, PaginateInit,
    LookUpInit, GetBasePath, ParseTypeChange, Wait) {
    
    ClearScope();

    // Inject dynamic view
    var defaultUrl = GetBasePath('inventory'),
        form = InventoryForm,
        generator = GenerateForm;

    form.well = true;
    form.formLabelSize = null;
    form.formFieldSize = null;

    generator.inject(form, { mode: 'add', related: false, scope: $scope });
    
    generator.reset();
    LoadBreadCrumbs();
    
    $scope.inventoryParseType = 'yaml';
    ParseTypeChange({ scope: $scope, variable: 'inventory_variables', parse_variable: 'inventoryParseType',
        field_id: 'inventory_inventory_variables' });

    LookUpInit({
        scope:  $scope,
        form: form,
        current_item: ($routeParams.organization_id) ? $routeParams.organization_id : null,
        list: OrganizationList,
        field: 'organization'
    });

    // Save
    $scope.formSave = function () {
        generator.clearApiErrors();
        Wait('start');
        try {
            var fld, json_data, data;

            // Make sure we have valid variable data
            if ( $scope.inventoryParseType === 'json') {
                json_data = JSON.parse( $scope.inventory_variables); //make sure JSON parses
            } else {
                json_data = jsyaml.load( $scope.inventory_variables); //parse yaml
            }

            // Make sure our JSON is actually an object
            if (typeof json_data !== 'object') {
                throw "failed to return an object!";
            }

            data = {};
            for (fld in form.fields) {
                if (fld !== 'inventory_variables') {
                    if (form.fields[fld].realName) {
                        data[form.fields[fld].realName] =  $scope[fld];
                    } else {
                        data[fld] =  $scope[fld];
                    }
                }
            }

            Rest.setUrl(defaultUrl);
            Rest.post(data)
                .success(function (data) {
                    var inventory_id = data.id;
                    if ($scope.inventory_variables) {
                        Rest.setUrl(data.related.variable_data);
                        Rest.put(json_data)
                            .success(function () {
                                Wait('stop');
                                $location.path('/inventories/' + inventory_id + '/');
                            })
                            .error(function (data, status) {
                                ProcessErrors( $scope, data, status, null, { hdr: 'Error!',
                                    msg: 'Failed to add inventory varaibles. PUT returned status: ' + status
                                });
                            });
                    } else {
                        Wait('stop');
                        $location.path('/inventories/' + inventory_id + '/');
                    }
                })
                .error(function (data, status) {
                    ProcessErrors( $scope, data, status, form, { hdr: 'Error!',
                        msg: 'Failed to add new inventory. Post returned status: ' + status });
                });
        } catch (err) {
            Wait('stop');
            Alert("Error", "Error parsing inventory variables. Parser returned: " + err);
        }

    };

    // Reset
    $scope.formReset = function () {
        generator.reset();
    };
}

InventoriesAdd.$inject = ['$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryForm', 'GenerateForm',
    'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'GenerateList', 'OrganizationList', 'SearchInit',
    'PaginateInit', 'LookUpInit', 'GetBasePath', 'ParseTypeChange', 'Wait'
];



function InventoriesEdit($scope, $location, $routeParams, $compile, GenerateList, ClearScope, InventoryGroups, InventoryHosts, BuildTree, Wait,
    GetSyncStatusMsg, InjectHosts, HostsReload, GroupsEdit, GroupsDelete, Breadcrumbs, LoadBreadCrumbs, Empty, Rest, ProcessErrors,
    InventoryUpdate, Alert, ToggleChildren, ViewUpdateStatus, GroupsCancelUpdate, Find, EditInventoryProperties, HostsEdit,
    HostsDelete, ToggleHostEnabled, CopyMoveGroup, CopyMoveHost, Stream, GetBasePath, ShowJobSummary, ApplyEllipsis, WatchInventoryWindowResize,
    HelpDialog, InventoryGroupsHelp, Store, ViewJob) {
    
    ClearScope();

    var generator = GenerateList,
        list = InventoryGroups;

    $scope.inventory_id = $routeParams.inventory_id;

    LoadBreadCrumbs({
        path: $location.path(),
        title: '{{ inventory_name }}'
    });

    // After the tree data loads for the first time, generate the groups and hosts lists
    if ($scope.removeGroupTreeLoaded) {
        $scope.removeGroupTreeLoaded();
    }
    $scope.removeGroupTreeLoaded = $scope.$on('GroupTreeLoaded', function (event, inventory_name, groups) {
        // Add breadcrumbs
        var e, inventoryAutoHelp;
        e = angular.element(document.getElementById('breadcrumbs'));
        e.html(Breadcrumbs({ list: list, mode: 'edit' }));
        $compile(e)($scope);

        // Add groups view
        generator.inject(list, {
            mode: 'edit',
            id: 'groups-container',
            breadCrumbs: false,
            searchSize: 'col-lg-5 col-md-5 col-sm-5'
        });
        $scope.groups = groups;
        $scope.inventory_name = inventory_name;

        // Default the selected group to the first node
        if ($scope.groups.length > 0) {
            $scope.selected_tree_id = $scope.groups[0].id;
            $scope.selected_group_id = $scope.groups[0].group_id;
            $scope.groups[0].selected_class = 'selected';
            $scope.groups[0].active_class = 'active-row';
            $scope.selected_group_name = $scope.groups[0].name;
        } else {
            $scope.selected_tree_id = null;
            $scope.selected_group_id = null;
        }

        // Add hosts view
        $scope.show_failures = false;
        InjectHosts({
            scope: $scope,
            inventory_id: $scope.inventory_id,
            tree_id: $scope.selected_tree_id,
            group_id: $scope.selected_group_id
        });

        // As the window shrinks and expands, apply ellipsis
        setTimeout(function () {
            // Hack to keep group name from slipping to a new line
            $('#groups_table .name-column').each(function () {
                var td_width, level_width, level_padding, level, pct;
                td_width = $(this).width();
                level_width = $(this).find('.level').width();
                level_padding = parseInt($(this).find('.level').css('padding-left').replace(/px/, ''));
                level = level_width + level_padding;
                pct = (100 - Math.ceil((level / td_width) * 100)) + '%';
                $(this).find('.group-name').css({
                    width: pct
                });
            });
            ApplyEllipsis('#groups_table .group-name a');
            ApplyEllipsis('#hosts_table .host-name a');
        }, 2500); //give the window time to display
        WatchInventoryWindowResize();

        inventoryAutoHelp = Store('inventoryAutoHelp');
        if (inventoryAutoHelp !== 'off' && $scope.autoShowGroupHelp) {
            $scope.showGroupHelp({
                autoShow: true
            });
        }

    });


    // Called after tree data is reloaded on refresh button click.
    if ($scope.removeGroupTreeRefreshed) {
        $scope.removeGroupTreeRefreshed();
    }
    $scope.removeGroupTreeRefreshed = $scope.$on('GroupTreeRefreshed', function () {
        // Reapply ellipsis to groups
        setTimeout(function () {
            ApplyEllipsis('#groups_table .group-name a');
        }, 2500);
        // Reselect the preveiously selected group node, causing host view to refresh.
        $scope.showHosts($scope.selected_tree_id, $scope.selected_group_id, false);
    });

    // Group was deleted. Now we need to refresh the group view.
    if ($scope.removeGroupDeleteCompleted) {
        $scope.removeGroupDeleteCompleted();
    }
    $scope.removeGroupDeleteCompleted = $scope.$on('GroupDeleteCompleted', function () {
        $scope.selected_tree_id = 1;
        $scope.selected_group_id = null;
        BuildTree({
            scope: $scope,
            inventory_id: $scope.inventory_id,
            refresh: true
        });
    });

    // Respond to a group drag-n-drop
    if ($scope.removeCopMoveGroup) {
        $scope.removeCopyMoveGroup();
    }
    $scope.removeCopyMoveGroup = $scope.$on('CopyMoveGroup', function (e, inbound_tree_id, target_tree_id) {
        CopyMoveGroup({
            scope: $scope,
            target_tree_id: target_tree_id,
            inbound_tree_id: inbound_tree_id
        });
    });

    // Respond to a host drag-n-drop
    if ($scope.removeCopMoveHost) {
        $scope.removeCopyMoveHost();
    }
    $scope.removeCopyMoveHost = $scope.$on('CopyMoveHost', function (e, target_tree_id, host_id) {
        CopyMoveHost({
            scope: $scope,
            target_tree_id: target_tree_id,
            host_id: host_id
        });
    });

    $scope.showHosts = function (tree_id, group_id, show_failures) {
        // Clicked on group
        if (tree_id !== null) {
            Wait('start');
            $scope.selected_tree_id = tree_id;
            $scope.selected_group_id = group_id;
            $scope.hosts = [];
            $scope.show_failures = show_failures; // turn on failed hosts filter in hosts view
            for (var i = 0; i < $scope.groups.length; i++) {
                if ($scope.groups[i].id === tree_id) {
                    $scope.groups[i].selected_class = 'selected';
                    $scope.groups[i].active_class = 'active-row';
                    $scope.selected_group_name = $scope.groups[i].name;
                } else {
                    $scope.groups[i].selected_class = '';
                    $scope.groups[i].active_class = '';
                }
            }
            if (Empty($scope.inventory_id)) {
                $scope.inventory_id = $scope.groups[0].inentory_id;
            }
            HostsReload({
                scope: $scope,
                group_id: group_id,
                tree_id: tree_id,
                inventory_id: $scope.inventory_id
            });
        } else {
            Wait('stop');
        }
    };

    $scope.createGroup = function () {
        GroupsEdit({
            scope: $scope,
            inventory_id: $scope.inventory_id,
            group_id: $scope.selected_group_id,
            mode: 'add'
        });
    };

    $scope.editGroup = function (group_id, tree_id) {
        GroupsEdit({
            scope: $scope,
            inventory_id: $scope.inventory_id,
            group_id: group_id,
            tree_id: tree_id,
            groups_reload: true,
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
                    group.name + '</em>. Use the Refresh button to monitor the status.', 'alert-info');
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
                            tree_id: group.id,
                            group_id: group.group_id
                        });
                    })
                    .error(function (data, status) {
                        Wait('stop');
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to retrieve inventory source: ' +
                            group.related.inventory_source + ' POST returned status: ' + status });
                    });
            }
        }
    };

    $scope.cancelUpdate = function (tree_id) {
        GroupsCancelUpdate({ scope: $scope, tree_id: tree_id });
    };

    $scope.toggle = function (tree_id) {
        // Expand/collapse nodes
        ToggleChildren({ scope: $scope, list: list, id: tree_id });
    };

    $scope.refreshGroups = function (tree_id, group_id) {
        // Refresh the tree data when refresh button cicked
        if (tree_id) {
            $scope.selected_tree_id = tree_id;
            $scope.selected_group_id = group_id;
        }
        BuildTree({ scope: $scope, inventory_id: $scope.inventory_id, refresh: true });
    };

    $scope.viewUpdateStatus = function (tree_id, group_id) {
        ViewUpdateStatus({
            scope: $scope,
            tree_id: tree_id,
            group_id: group_id
        });
    };

    $scope.deleteGroup = function (tree_id, group_id) {
        GroupsDelete({
            scope: $scope,
            tree_id: tree_id,
            group_id: group_id,
            inventory_id: $scope.inventory_id
        });
    };

    $scope.createHost = function () {
        HostsEdit({ scope: $scope, mode: 'add', host_id: null, selected_group_id: $scope.selected_tree_id, inventory_id: $scope.inventory_id });
    };

    $scope.editInventoryProperties = function () {
        EditInventoryProperties({ scope: $scope, inventory_id: $scope.inventory_id });
    };

    $scope.editHost = function (host_id) {
        HostsEdit({ scope: $scope, mode: 'edit', host_id: host_id, inventory_id: $scope.inventory_id });
    };

    $scope.deleteHost = function (host_id, host_name) {
        HostsDelete({ scope: $scope, host_id: host_id, host_name: host_name });
    };

    $scope.toggleHostEnabled = function (host_id, external_source) {
        ToggleHostEnabled({ scope: $scope, host_id: host_id, external_source: external_source });
    };

    $scope.showGroupActivity = function () {
        var url, title, group;
        if ($scope.selected_group_id) {
            group = Find({
                list: $scope.groups,
                key: 'id',
                val: $scope.selected_tree_id
            });
            url = GetBasePath('activity_stream') + '?group__id=' + $scope.selected_group_id;
            title = 'Showing all activities for group ' + group.name;
        } else {
            title = 'Showing all activities for all ' + $scope.inventory_name + ' groups';
            url = GetBasePath('activity_stream') + '?group__inventory__id=' + $scope.inventory_id;
        }
        Stream({
            scope: $scope,
            inventory_name: $scope.inventory_name,
            url: url,
            title: title
        });
    };

    $scope.showHostActivity = function () {
        var url, title;
        title = 'Showing all activities for all ' + $scope.inventory_name + ' hosts';
        url = GetBasePath('activity_stream') + '?host__inventory__id=' + $scope.inventory_id;
        Stream({
            scope: $scope,
            inventory_name: $scope.inventory_name,
            url: url,
            title: title
        });
    };

    $scope.showJobSummary = function (job_id) {
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
    };

    $scope.viewJob = function(id) {
        ViewJob({ scope: $scope, id: id });
    };

    //Load tree data for the first time
    BuildTree({
        scope: $scope,
        inventory_id: $scope.inventory_id,
        refresh: false
    });

}

InventoriesEdit.$inject = ['$scope', '$location', '$routeParams', '$compile', 'GenerateList', 'ClearScope', 'InventoryGroups', 'InventoryHosts',
    'BuildTree', 'Wait', 'GetSyncStatusMsg', 'InjectHosts', 'HostsReload', 'GroupsEdit', 'GroupsDelete', 'Breadcrumbs',
    'LoadBreadCrumbs', 'Empty', 'Rest', 'ProcessErrors', 'InventoryUpdate', 'Alert', 'ToggleChildren', 'ViewUpdateStatus', 'GroupsCancelUpdate',
    'Find', 'EditInventoryProperties', 'HostsEdit', 'HostsDelete', 'ToggleHostEnabled', 'CopyMoveGroup', 'CopyMoveHost',
    'Stream', 'GetBasePath', 'ShowJobSummary', 'ApplyEllipsis', 'WatchInventoryWindowResize', 'HelpDialog', 'InventoryGroupsHelp', 'Store',
    'ViewJob'
];
