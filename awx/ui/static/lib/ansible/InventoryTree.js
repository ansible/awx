/************************************
 *
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
  /**
 *  @ngdoc function
 *  @name lib.ansible.function:inventoryTree
 *  @description
 *  InventoryTree.js
 *
 *  Build data for the tree selector table used on inventory detail page.
 *
 */

'use strict';

angular.module('InventoryTree', ['Utilities', 'RestServices', 'GroupsHelper', 'PromptDialog'])

.factory('SortNodes', [
    function () {
        return function (data) {
            //Sort nodes by name
            var i, j, names = [], newData = [];
            for (i = 0; i < data.length; i++) {
                names.push(data[i].name);
            }
            names.sort();
            for (j = 0; j < names.length; j++) {
                for (i = 0; i < data.length; i++) {
                    if (data[i].name === names[j]) {
                        newData.push(data[i]);
                    }
                }
            }
            return newData;
        };
    }
])

.factory('BuildTree', ['$location', 'Rest', 'GetBasePath', 'ProcessErrors', 'SortNodes', 'Wait', 'GetSyncStatusMsg', 'GetHostsStatusMsg', 'Store',
    function ($location, Rest, GetBasePath, ProcessErrors, SortNodes, Wait, GetSyncStatusMsg, GetHostsStatusMsg, Store) {
        return function (params) {

            var inventory_id = params.inventory_id,
                scope = params.scope,
                refresh = params.refresh,
                emit = params.emit,
                new_group_id = params.new_group_id,
                groups = [],
                id = 1,
                local_child_store,
                path = $location.path();

            function buildAllHosts(tree_data) {
                // Start our tree object with All Hosts
                var children = [],
                    sorted = SortNodes(tree_data),
                    j, all_hosts;

                for (j = 0; j < sorted.length; j++) {
                    children.push(sorted[j].id);
                }

                all_hosts = {
                    name: 'All Hosts',
                    id: 1,
                    group_id: null,
                    parent: 0,
                    description: '',
                    show: true,
                    ngicon: null,
                    has_children: false,
                    related: {},
                    selected_class: '',
                    show_failures: false,
                    isDraggable: false,
                    isDroppable: true,
                    children: children
                };
                groups.push(all_hosts);
            }

            function getExpandState(key) {
                var result = true;
                local_child_store.every(function(child) {
                    if (child.key === key) {
                        result = child.expand;
                        return false;
                    }
                    return true;
                });
                return result;
            }

            function getShowState(key) {
                var result = null;
                local_child_store.every(function(child) {
                    if (child.key === key) {
                        result = (child.show !== undefined) ? child.show : true;
                        return false;
                    }
                    return true;
                });
                return result;
            }

            function buildGroups(tree_data, parent, level) {

                var children, stat, hosts_status, group,
                    sorted = SortNodes(tree_data),
                    expand, show;

                sorted.forEach( function(row, i) {
                    id++;

                    stat = GetSyncStatusMsg({
                        status: sorted[i].summary_fields.inventory_source.status,
                        has_inventory_sources: sorted[i].has_inventory_sources,
                        source: ( (sorted[i].summary_fields.inventory_source) ? sorted[i].summary_fields.inventory_source.source : null )
                    }); // from helpers/Groups.js

                    hosts_status = GetHostsStatusMsg({
                        active_failures: sorted[i].hosts_with_active_failures,
                        total_hosts: sorted[i].total_hosts,
                        inventory_id: inventory_id,
                        group_id: sorted[i].id
                    }); // from helpers/Groups.js

                    children = [];
                    sorted[i].children.forEach( function(child, j) {
                        children.push(sorted[i].children[j].id);
                    });

                    expand = (sorted[i].children.length > 0) ? getExpandState(sorted[i].id) : false;
                    show = getShowState(sorted[i].id);
                    if (show === null) {
                        // this is a node we haven't seen before, so check the parent expand/collapse state
                        // If parent is not expanded, then child should be hidden.
                        show = true;
                        if (parent > 0) {
                            groups.every(function(g) {
                                if (g.id === parent) {
                                    show = getExpandState(g.key);
                                    return false;
                                }
                                return true;
                            });
                        }
                    }

                    group = {
                        name: sorted[i].name,
                        has_active_failures: sorted[i].has_active_failures,
                        total_hosts: sorted[i].total_hosts,
                        hosts_with_active_failures: sorted[i].hosts_with_active_failures,
                        total_groups: sorted[i].total_groups,
                        groups_with_active_failures: sorted[i].groups_with_active_failures,
                        parent: parent,
                        has_children: (sorted[i].children.length > 0) ? true : false,
                        has_inventory_sources: sorted[i].has_inventory_sources,
                        id: id,
                        source: sorted[i].summary_fields.inventory_source.source,
                        key: sorted[i].id,
                        group_id: sorted[i].id,
                        event_level: level,
                        children: children,
                        show: show,
                        related: sorted[i].related,
                        status: sorted[i].summary_fields.inventory_source.status,
                        status_class: stat['class'],
                        status_tooltip: stat.tooltip,
                        launch_tooltip: stat.launch_tip,
                        launch_class: stat.launch_class,
                        hosts_status_tip: hosts_status.tooltip,
                        show_failures: hosts_status.failures,
                        hosts_status_class: hosts_status['class'],
                        inventory_id: inventory_id,
                        selected_class: '',
                        isDraggable: true,
                        isDroppable: true
                    };
                    if (sorted[i].children.length > 0)  {
                        if (expand) {
                            group.ngicon = 'fa fa-minus-square-o node-toggle';
                        }
                        else {
                            group.ngicon = 'fa fa-plus-square-o node-toggle';
                        }
                    }
                    else {
                        group.ngicon = 'fa fa-square-o node-no-toggle';
                    }
                    if (new_group_id && group.group_id === new_group_id) {
                        scope.selected_tree_id = id;
                        scope.selected_group_id = group.group_id;
                    }
                    groups.push(group);
                    if (sorted[i].children.length > 0) {
                        buildGroups(sorted[i].children, id, level + 1);
                    }
                });
            }

            // Build the HTML for our tree
            if (scope.buildAllGroupsRemove) {
                scope.buildAllGroupsRemove();
            }
            scope.buildAllGroupsRemove = scope.$on('buildAllGroups', function (e, inventory_name, inventory_tree) {
                Rest.setUrl(inventory_tree);
                Rest.get()
                    .success(function (data) {
                        buildAllHosts(data);
                        buildGroups(data, 0, 0);
                        scope.autoShowGroupHelp = (data.length === 0) ? true : false;
                        if (refresh) {
                            scope.groups = groups;
                            scope.$emit('GroupTreeRefreshed', inventory_name, groups, emit);
                        } else {
                            scope.$emit('GroupTreeLoaded', inventory_name, groups, emit);
                        }
                    })
                    .error(function (data, status) {
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to get inventory tree for: ' + inventory_id + '. GET returned: ' + status
                        });
                    });
            });


            function loadTreeData() {
                // Load the inventory root node
                Wait('start');
                Rest.setUrl(GetBasePath('inventory') + inventory_id + '/');
                Rest.get()
                    .success(function (data) {
                        scope.$emit('buildAllGroups', data.name, data.related.tree, data.related.groups);
                    })
                    .error(function (data, status) {
                        Wait('stop');
                        ProcessErrors(scope, data, status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get inventory: ' + inventory_id + '. GET returned: ' + status
                        });
                    });
            }
            local_child_store = Store(path + '_children');
            if (!local_child_store) {
                local_child_store = [];
            }
            loadTreeData();
        };
    }
])


// Update a group with a set of properties
.factory('UpdateGroup', ['ApplyEllipsis', 'GetSyncStatusMsg', 'Empty',
    function (ApplyEllipsis, GetSyncStatusMsg, Empty) {
        return function (params) {

            var scope = params.scope,
                group_id = params.group_id,
                properties = params.properties,
                i, p, grp, old_name, stat;

            for (i = 0; i < scope.groups.length; i++) {
                if (scope.groups[i].id === group_id) {
                    grp = scope.groups[i];
                    for (p in properties) {
                        if (p === 'name') {
                            old_name = scope.groups[i].name;
                        }
                        if (p === 'source') {
                            if (properties[p] !== scope.groups[i][p]) {
                                // User changed source
                                if (!Empty(properties[p]) && (scope.groups[i].status === 'none' || Empty(scope.groups[i].status))) {
                                    // We have a source but no status, seed the status with 'never' to enable sync button
                                    scope.groups[i].status = 'never updated';
                                } else if (!properties[p]) {
                                    // User removed source
                                    scope.groups[i].status = 'none';
                                }
                                // Update date sync status links/icons
                                stat = GetSyncStatusMsg({
                                    status: scope.groups[i].status,
                                    has_inventory_sources: properties.has_inventory_sources,
                                    source: properties.source
                                });
                                scope.groups[i].status_class = stat['class'];
                                scope.groups[i].status_tooltip = stat.tooltip;
                                scope.groups[i].launch_tooltip = stat.launch_tip;
                                scope.groups[i].launch_class = stat.launch_class;
                            }
                        }
                        scope.groups[i][p] = properties[p];
                    }
                }
                /*if (scope.groups[i].id === scope.selected_tree_id) {
                    //Make sure potential group name change gets reflected throughout the page
                    scope.selected_group_name = scope.groups[i].name;
                    scope.search_place_holder = 'Search ' + scope.groups[i].name;
                    scope.hostSearchPlaceholder = 'Search ' + scope.groups[i].name;
                }*/
            }

            // Update any titles attributes created by ApplyEllipsis
            if (old_name) {
                setTimeout(function () {
                    $('#groups_table .group-name a[title="' + old_name + '"]').attr('title', properties.name);
                    ApplyEllipsis('#groups_table .group-name a');
                }, 2500);
            }

        };
    }
])


// Set node name and description after an update to Group properties.
.factory('SetNodeName', [
    function () {
        return function (params) {
            var name = params.name,
                descr = params.description,
                group_id = (params.group_id !== undefined) ? params.group_id : null,
                inventory_id = (params.inventory_id !== undefined) ? params.inventory_id : null;

            if (group_id !== null) {
                $('#inventory-tree').find('li [data-group-id="' + group_id + '"]').each(function () {
                    $(this).attr('data-name', name);
                    $(this).attr('data-description', descr);
                    $(this).find('.activate').first().text(name);
                });
            }

            if (inventory_id !== null) {
                $('#inventory-root-node').attr('data-name', name).attr('data-description', descr).find('.activate').first().text(name);
            }
        };
    }
])


// Copy or Move a group on the tree after drag-n-drop
.factory('CopyMoveGroup', ['$compile', 'Alert', 'ProcessErrors', 'Find', 'Wait', 'Rest', 'Empty', 'GetBasePath',
    function ($compile, Alert, ProcessErrors, Find, Wait, Rest, Empty, GetBasePath) {
        return function (params) {

            var scope = params.scope,
                target = Find({ list: scope.groups, key: 'id', val: params.target_tree_id }),
                inbound = Find({ list: scope.groups, key: 'id', val: params.inbound_tree_id }),
                e, html = '';

            // Build the html for our prompt dialog
            html += "<div id=\"copy-prompt-modal\" class=\"modal fade\">\n";
            html += "<div class=\"modal-dialog\">\n";
            html += "<div class=\"modal-content\">\n";
            html += "<div class=\"modal-header\">\n";
            html += "<button type=\"button\" class=\"close\" data-target=\"#copy-prompt-modal\" " +
                "data-dismiss=\"modal\" aria-hidden=\"true\">&times;</button>\n";

            if (target.id === 1 || inbound.parent === 0) {
                // We're moving the group to the top level, or we're moving a top level group down
                html += "<h3>Move Group</h3>\n";
            } else {
                html += "<h3>Copy or Move?</h3>\n";
            }

            html += "</div>\n";
            html += "<div class=\"modal-body\">\n";

            if (target.id === 1) {
                html += "<div class=\"alert alert-info\">Are you sure you want to move group " + inbound.name + " to the top level?</div>";
            } else if (inbound.parent === 0) {
                html += "<div class=\"alert alert-info\">Are you sure you want to move group " + inbound.name + " from the top level and make it a child of " +
                    target.name + "?</div>";
            } else {
                html += "<div class=\"text-center\">\n";
                html += "<p>Would you like to copy or move group <em>" + inbound.name + "</em> to group <em>" + target.name + "</em>?</p>\n";
                html += "<div style=\"margin-top: 30px;\">\n";
                html += "<a href=\"\" ng-click=\"moveGroup()\" class=\"btn btn-primary\" style=\"margin-right: 15px;\"><i class=\"fa fa-cut\"></i> Move</a>\n";
                html += "<a href=\"\" ng-click=\"copyGroup()\" class=\"btn btn-primary\"><i class=\"fa fa-copy\"></i> Copy</a>\n";
                html += "</div>\n";
                html += "</div>\n";
            }

            html += "</div>\n";
            html += "<div class=\"modal-footer\">\n";
            html += "<a href=\"#\" data-target=\"#prompt-modal\" data-dismiss=\"modal\" class=\"btn btn-default\">Cancel</a>\n";

            if (target.id === 1 || inbound.parent === 0) {
                // We're moving the group to the top level, or we're moving a top level group down
                html += "<a href=\"\" data-target=\"#prompt-modal\" ng-click=\"moveGroup()\" class=\"btn btn-primary\">Yes</a>\n";
            }

            html += "</div>\n";
            html += "</div><!-- modal-content -->\n";
            html += "</div><!-- modal-dialog -->\n";
            html += "</div><!-- modal -->\n";

            // Inject our custom dialog
            e= angular.element(document.getElementById('inventory-modal-container'));
            e.empty().append(html);
            $compile(e)(scope);

            // Display it
            $('#copy-prompt-modal').modal({
                backdrop: 'static',
                keyboard: true,
                show: true
            });

            // Respond to move
            scope.moveGroup = function () {
                var url, group, parent;
                $('#copy-prompt-modal').modal('hide');
                Wait('start');

                // disassociate the group from the original parent
                if (scope.removeGroupRemove) {
                    scope.removeGroupRemove();
                }
                scope.removeGroupRemove = scope.$on('removeGroup', function () {
                    if (inbound.parent > 0) {
                        // Only remove a group from a parent when the parent is a group and not the inventory root
                        parent = Find({ list: scope.groups, key: 'id', val: inbound.parent });
                        url = GetBasePath('base') + 'groups/' + parent.group_id + '/children/';
                        Rest.setUrl(url);
                        Rest.post({ id: inbound.group_id, disassociate: 1 })
                            .success(function () {
                                //Triggers refresh of group list in inventory controller
                                scope.$emit('GroupDeleteCompleted');
                            })
                            .error(function (data, status) {
                                Wait('stop');
                                ProcessErrors(scope, data, status, null, {
                                    hdr: 'Error!',
                                    msg: 'Failed to remove ' + inbound.name +
                                        ' from ' + parent.name + '. POST returned status: ' + status
                                });
                            });
                    } else {
                        //Triggers refresh of group list in inventory controller
                        scope.$emit('GroupDeleteCompleted');
                    }
                });

                // add the new group to the target parent
                url = (!Empty(target.group_id)) ?
                    GetBasePath('base') + 'groups/' + target.group_id + '/children/' :
                    GetBasePath('inventory') + scope.inventory_id + '/groups/';
                group = {
                    id: inbound.group_id,
                    name: inbound.name,
                    description: inbound.description,
                    inventory: scope.inventory_id
                };
                Rest.setUrl(url);
                Rest.post(group)
                    .success(function () {
                        scope.$emit('removeGroup');
                    })
                    .error(function (data, status) {
                        var target_name = (Empty(target.group_id)) ? 'inventory' : target.name;
                        Wait('stop');
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to add ' + inbound.name + ' to ' + target_name + '. POST returned status: ' + status });
                    });
            };


            scope.copyGroup = function () {
                $('#copy-prompt-modal').modal('hide');
                Wait('start');
                // add the new group to the target parent
                var url = (!Empty(target.group_id)) ?
                        GetBasePath('base') + 'groups/' + target.group_id + '/children/' :
                        GetBasePath('inventory') + scope.inventory_id + '/groups/',
                    group = {
                        id: inbound.group_id,
                        name: inbound.name,
                        description: inbound.description,
                        inventory: scope.inventory_id
                    };

                Rest.setUrl(url);
                Rest.post(group)
                    .success(function () {
                        //Triggers refresh of group list in inventory controller
                        scope.$emit('GroupDeleteCompleted');
                    })
                    .error(function (data, status) {
                        var target_name = (Empty(target.group_id)) ? 'inventory' : target.name;
                        Wait('stop');
                        ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                            msg: 'Failed to add ' + inbound.name + ' to ' + target_name + '. POST returned status: ' + status
                        });
                    });
            };

        };
    }
])

// Copy a host after drag-n-drop
.factory('CopyMoveHost', ['$compile', 'Alert', 'ProcessErrors', 'Find', 'Wait', 'Rest', 'Empty', 'GetBasePath',
    function ($compile, Alert, ProcessErrors, Find, Wait, Rest, Empty, GetBasePath) {
        return function (params) {

            var scope = params.scope,
                target = Find({ list: scope.groups, key: 'id', val: params.target_tree_id }),
                host = Find({ list: scope.hosts, key: 'id', val: params.host_id }),
                found = false, e, i, html = '';

            if (host.summary_fields.all_groups) {
                for (i = 0; i < host.summary_fields.all_groups.length; i++) {
                    if (host.summary_fields.all_groups[i].id === target.group_id) {
                        found = true;
                        break;
                    }
                }
            }
            if (found) {
                html += "<div id=\"copy-alert-modal\" class=\"modal fade\">\n";
                html += "<div class=\"modal-dialog\">\n";
                html += "<div class=\"modal-content\">\n";
                html += "<div class=\"modal-header\">\n";
                html += "<button type=\"button\" class=\"close\" ng-hide=\"disableButtons\" data-target=\"#copy-alert-modal\"\n";
                html += "data-dismiss=\"modal\" class=\"modal\" aria-hidden=\"true\">&times;</button>\n";
                html += "<h3>Already in Group</h3>\n";
                html += "</div>\n";
                html += "<div class=\"modal-body\">\n";
                html += "<div class=\"alert alert-info\"><p>Host " + host.name + " is already in group " + target.name + ".</p></div>\n";
                html += "</div>\n";
                html += "<div class=\"modal-footer\">\n";
                html += "<a href=\"#\" data-target=\"#copy-alert-modal\" data-dismiss=\"modal\" class=\"btn btn-primary\">OK</a>\n";
                html += "</div>\n";
                html += "</div>\n";
                html += "</div>\n";
                html += "</div>\n";

                // Inject our custom dialog
                e = angular.element(document.getElementById('inventory-modal-container'));
                e.empty().append(html);
                $compile(e)(scope);

                // Display it
                $('#copy-alert-modal').modal({
                    backdrop: 'static',
                    keyboard: true,
                    show: true
                });

            } else {
                // Build the html for our prompt dialog
                html = '';
                html += "<div id=\"copy-prompt-modal\" class=\"modal fade\">\n";
                html += "<div class=\"modal-dialog\">\n";
                html += "<div class=\"modal-content\">\n";
                html += "<div class=\"modal-header\">\n";
                html += "<button type=\"button\" class=\"close\" data-target=\"#copy-prompt-modal\" " +
                    "data-dismiss=\"modal\" aria-hidden=\"true\">&times;</button>\n";
                html += "<h3>Copy Host</h3>\n";
                html += "</div>\n";
                html += "<div class=\"modal-body\">\n";
                html += "<div class=\"alert alert-info\">Are you sure you want to copy host " + host.name + ' to group ' + target.name + '?</div>';
                html += "</div>\n";
                html += "<div class=\"modal-footer\">\n";
                html += "<a href=\"#\" data-target=\"#prompt-modal\" data-dismiss=\"modal\" class=\"btn btn-default\">No</a>\n";
                html += "<a href=\"\" data-target=\"#prompt-modal\" ng-click=\"copyHost()\" class=\"btn btn-primary\">Yes</a>\n";
                html += "</div>\n";
                html += "</div><!-- modal-content -->\n";
                html += "</div><!-- modal-dialog -->\n";
                html += "</div><!-- modal -->\n";

                // Inject our custom dialog
                e = angular.element(document.getElementById('inventory-modal-container'));
                e.empty().append(html);
                $compile(e)(scope);

                // Display it
                $('#copy-prompt-modal').modal({
                    backdrop: 'static',
                    keyboard: true,
                    show: true
                });

                scope.copyHost = function () {
                    $('#copy-prompt-modal').modal('hide');
                    Wait('start');
                    Rest.setUrl(GetBasePath('groups') + target.group_id + '/hosts/');
                    Rest.post(host)
                        .success(function () {
                            // Signal the controller to refresh the hosts view
                            scope.$emit('GroupTreeRefreshed');
                        })
                        .error(function (data, status) {
                            Wait('stop');
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!', msg: 'Failed to add ' + host.name + ' to ' +
                                    target.name + '. POST returned status: ' + status });
                        });
                };
            }
        };
    }
]);