
/************************************
 *
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryTree.js
 *
 *  Build data for the tree selector table used on inventory detail page.
 *
 */

'use strict';

angular.module('InventoryTree', ['Utilities', 'RestServices', 'GroupsHelper', 'PromptDialog'])
    
    .factory('SortNodes', [ function() {
        return function(data) {
            //Sort nodes by name
            var names = [];
            var newData = [];
            for (var i=0; i < data.length; i++) {
                names.push(data[i].name);
            }
            names.sort();
            for (var j=0; j < names.length; j++) {
                for (i=0; i < data.length; i++) {
                    if (data[i].name == names[j]) {
                       newData.push(data[i]);
                    }
                }
            }
            return newData;
            }
            }])

    .factory('BuildTree', ['Rest', 'GetBasePath', 'ProcessErrors', 'SortNodes', 'Wait', 'GetSyncStatusMsg', 'GetHostsStatusMsg',
        function(Rest, GetBasePath, ProcessErrors, SortNodes, Wait, GetSyncStatusMsg, GetHostsStatusMsg) {
        return function(params) {
            
            var inventory_id = params.inventory_id;
            var scope = params.scope;
            var refresh = params.refresh;
            var emit = params.emit;
            var new_group_id = params.new_group_id;
            var groups = [];
            var id = 1;
            
            function buildAllHosts(tree_data) {
                // Start our tree object with All Hosts
                var children = [];
                var sorted = SortNodes(tree_data);
                for (var j=0; j < sorted.length; j++) {
                     children.push(sorted[j].id);
                }  
                var all_hosts = {
                    name: 'All Hosts', id: 1, group_id: null, parent: 0, description: '', show: true, ngicon: null,
                    has_children: false, related: {}, selected_class: '', show_failures: false, isDraggable: false, 
                    isDroppable: true, children: children };
                groups.push(all_hosts);
                }

            function buildGroups(tree_data, parent, level) {
                var sorted = SortNodes(tree_data);
                for (var i=0; i < sorted.length; i++) {
                    id++;
                    
                    var stat = GetSyncStatusMsg({ 
                        status: sorted[i].summary_fields.inventory_source.status
                        });   // from helpers/Groups.js
                    
                    var hosts_status = GetHostsStatusMsg({ 
                        active_failures: sorted[i].hosts_with_active_failures,
                        total_hosts: sorted[i].total_hosts,
                        inventory_id: inventory_id, 
                        group_id: sorted[i].id
                        });   // from helpers/Groups.js
                    
                    var children = [];
                    for (var j=0; j < sorted[i].children.length; j++) {
                        children.push(sorted[i].children[j].id);
                    }    
                    
                    var group = {
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
                        group_id: sorted[i].id,
                        event_level: level,
                        children: children,
                        ngicon: (sorted[i].children.length > 0) ? 'fa fa-minus-square-o node-toggle' : 'fa fa-square-o node-no-toggle',
                        ngclick: 'toggle(' + id + ')',
                        related: { 
                            children: (sorted[i].children.length > 0) ? sorted[i].related.children : '', 
                            inventory_source: sorted[i].related.inventory_source
                          },
                        status: sorted[i].summary_fields.inventory_source.status,
                        status_class: stat['class'],
                        status_tooltip: stat['tooltip'],
                        launch_tooltip: stat['launch_tip'],
                        launch_class: stat['launch_class'],
                        hosts_status_tip: hosts_status['tooltip'],
                        show_failures: hosts_status['failures'],
                        hosts_status_class: hosts_status['class'],
                        selected_class: '',
                        show: true,
                        isDraggable: true, 
                        isDroppable: true
                        }
                    groups.push(group);
                    if (new_group_id && group.group_id == new_group_id) {
                        // For new group
                        scope.selected_tree_id = id;
                        scope.selected_group_id = group.group_id;
                    }
                    if (sorted[i].children.length > 0) {
                        buildGroups(sorted[i].children, id, level + 1);
                    }
                }
            }

            // Build the HTML for our tree
            if (scope.buildAllGroupsRemove) {
                scope.buildAllGroupsRemove();
            }
            scope.buildAllGroupsRemove = scope.$on('buildAllGroups', function(e, inventory_name, inventory_tree) {
                Rest.setUrl(inventory_tree);
                Rest.get()
                    .success( function(data, status, headers, config) {
                        buildAllHosts(data);
                        buildGroups(data, 0, 0);
                        scope.autoShowGroupHelp = (data.length == 0) ? true : false;
                        if (refresh) {
                            scope.groups = groups;
                            scope.$emit('GroupTreeRefreshed', inventory_name, groups, emit);
                        }
                        else {
                            scope.$emit('GroupTreeLoaded', inventory_name, groups, emit);
                        }
                        })
                    .error( function(data, status, headers, config) {
                        Wait('stop');
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Failed to get inventory tree for: ' + inventory_id + '. GET returned: ' + status });
                        });
                });
          
           
            function loadTreeData() {
                // Load the inventory root node
                Wait('start');
                Rest.setUrl (GetBasePath('inventory') + inventory_id + '/');
                Rest.get()
                    .success( function(data, status, headers, config) {
                        scope.$emit('buildAllGroups', data.name, data.related.tree, data.related.groups);
                        })
                    .error( function(data, status, headers, config) {
                        Wait('stop');
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Failed to get inventory: ' + inventory_id + '. GET returned: ' + status });
                        });
                }

            loadTreeData();
            }
            }])
    

    // Update a group with a set of properties 
    .factory('UpdateGroup', ['ApplyEllipsis', function(ApplyEllipsis) {
        return function(params) {
            
            var scope = params.scope; 
            var group_id = params.group_id; 
            var properties = params.properties;   // object of key:value pairs to update
            var old_name;
            for (var i=0; i < scope.groups.length; i++) {
                if (scope.groups[i].group_id == group_id) {
                    var grp = scope.groups[i]; 
                    for (var p in properties) {
                        if (p == 'name') {
                            old_name = scope.groups[i].name;
                        }
                        scope.groups[i][p] = properties[p];
                    }
                }
                if (scope.groups[i].id == scope.selected_tree_id) {
                    //Make sure potential group name change gets reflected throughout the page
                    scope.selected_group_name = scope.groups[i].name;
                    scope.search_place_holder = 'Search ' + scope.groups[i].name;
                    scope.hostSearchPlaceholder = 'Search ' + scope.groups[i].name;
                }
            }

            // Update any titles attributes created by ApplyEllipsis
            if (old_name) {
                setTimeout(function() { 
                    $('#groups_table .group-name a[title="' + old_name + '"').attr('title',properties.name);
                    ApplyEllipsis('#groups_table .group-name a');
                    }, 2500);
            }

            }
            }])


    // Set node name and description after an update to Group properties.
    .factory('SetNodeName', [ function() {
        return function(params) {
            var scope = params.scope;
            var name = params.name; 
            var descr = params.description; 
            var group_id = (params.group_id !== undefined) ? params.group_id : null;
            var inventory_id = (params.inventory_id != undefined) ? params.inventory_id : null; 

            if (group_id !== null) {
                $('#inventory-tree').find('li [data-group-id="' + group_id + '"]').each(function(idx) {
                    $(this).attr('data-name',name);
                    $(this).attr('data-description',descr);
                    $(this).find('.activate').first().text(name); 
                    });
            }

            if (inventory_id !== null) {
                $('#inventory-root-node').attr('data-name', name).attr('data-description', descr).find('.activate').first().text(name);
            }
            }
            }])
    

    // Copy or Move a group on the tree after drag-n-drop
    .factory('CopyMoveGroup', ['$compile', 'Alert', 'ProcessErrors', 'Find', 'Wait', 'Rest', 'Empty', 'GetBasePath',
        function($compile, Alert, ProcessErrors, Find, Wait, Rest, Empty, GetBasePath) {
        return function(params) {

            var scope = params.scope; 
            var target = Find({ list: scope.groups, key: 'id', val: params.target_tree_id });
            var inbound = Find({ list: scope.groups, key: 'id', val: params.inbound_tree_id });
            
            // Build the html for our prompt dialog
            var html = '';
            html += "<div id=\"copy-prompt-modal\" class=\"modal fade\">\n";
            html += "<div class=\"modal-dialog\">\n";
            html += "<div class=\"modal-content\">\n";
            html += "<div class=\"modal-header\">\n";
            html += "<button type=\"button\" class=\"close\" data-target=\"#copy-prompt-modal\" " + 
                "data-dismiss=\"modal\" aria-hidden=\"true\">&times;</button>\n";
            
            if (target.id == 1 || inbound.parent == 0) {
               // We're moving the group to the top level, or we're moving a top level group down
               html += "<h3>Move Group</h3>\n";
            }
            else {
               html += "<h3>Copy or Move?</h3>\n";
            }

            html += "</div>\n";
            html += "<div class=\"modal-body\">\n";
            
            if (target.id == 1) {
                html += "<p>Are you sure you want to move group " + inbound.name + " to the top level?</p>";
            }
            else if (inbound.parent == 0) {
                html += "<p>Are you sure you want to move group " + inbound.name + " from the top level and make it a child of " +
                    target.name + "?</p>";
            }
            else {
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

            if (target.id == 1 || inbound.parent == 0) {
                // We're moving the group to the top level, or we're moving a top level group down
                html += "<a href=\"\" data-target=\"#prompt-modal\" ng-click=\"moveGroup()\" class=\"btn btn-primary\">Yes</a>\n";
            }

            html += "</div>\n";
            html += "</div><!-- modal-content -->\n";
            html += "</div><!-- modal-dialog -->\n";
            html += "</div><!-- modal -->\n";
            
            // Inject our custom dialog
            var e = angular.element(document.getElementById('inventory-modal-container'));
            e.empty().append(html);
            $compile(e)(scope);
            
            // Display it
            $('#copy-prompt-modal').modal({
                backdrop: 'static',
                keyboard: true,
                show: true
                });
            
            // Respond to move 
            scope.moveGroup = function() {
                
                $('#copy-prompt-modal').modal('hide');
                Wait('start');
                
                // disassociate the group from the original parent
                if (scope.removeGroupRemove) {
                   scope.removeGroupRemove(); 
                }
                scope.removeGroupRemove = scope.$on('removeGroup', function() {
                    if (inbound.parent > 0) {
                        // Only remove a group from a parent when the parent is a group and not the inventory root
                        var parent = Find({ list: scope.groups, key: 'id', val: inbound.parent })
                        var url = GetBasePath('base') + 'groups/' + parent.group_id + '/children/';
                        Rest.setUrl(url);
                        Rest.post({ id: inbound.group_id, disassociate: 1 })
                            .success( function(data, status, headers, config) {
                                //Triggers refresh of group list in inventory controller
                                scope.$emit('GroupDeleteCompleted'); 
                                })
                            .error( function(data, status, headers, config) {
                                Wait('stop');
                                ProcessErrors(scope, data, status, null,
                                    { hdr: 'Error!', msg: 'Failed to remove ' + inbound.name + 
                                      ' from ' + parent.name + '. POST returned status: ' + status });
                                });
                    }
                    else {
                        //Triggers refresh of group list in inventory controller
                        scope.$emit('GroupDeleteCompleted'); 
                    }
                    });

                // add the new group to the target parent
                var url = (!Empty(target.group_id)) ? 
                    GetBasePath('base') + 'groups/' + target.group_id + '/children/' : 
                        GetBasePath('inventory') + scope.inventory_id + '/groups/';
                var group = { 
                    id: inbound.group_id,
                    name: inbound.name,
                    description: inbound.description,
                    inventory: scope.inventory_id
                    }
                Rest.setUrl(url);
                Rest.post(group)
                    .success( function(data, status, headers, config) {
                        scope.$emit('removeGroup');
                        })
                    .error( function(data, status, headers, config) {
                        var target_name = (Empty(target.group_id)) ? 'inventory' : target.name;
                        Wait('stop');
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Failed to add ' + node.attr('name') + ' to ' + 
                            target_name + '. POST returned status: ' + status });
                        });
                }
                

            scope.copyGroup = function() {
                $('#copy-prompt-modal').modal('hide');
                Wait('start');
                // add the new group to the target parent
                var url = (!Empty(target.group_id)) ? 
                    GetBasePath('base') + 'groups/' + target.group_id + '/children/' : 
                        GetBasePath('inventory') + scope.inventory_id + '/groups/';
                var group = { 
                    id: inbound.group_id,
                    name: inbound.name,
                    description: inbound.description,
                    inventory: scope.inventory_id
                    }
                Rest.setUrl(url);
                Rest.post(group)
                   .success( function(data, status, headers, config) {
                       //Triggers refresh of group list in inventory controller
                       scope.$emit('GroupDeleteCompleted'); 
                       })
                   .error( function(data, status, headers, config) {
                       var target_name = (Empty(target.group_id)) ? 'inventory' : target.name;
                       Wait('stop');
                       ProcessErrors(scope, data, status, null,
                          { hdr: 'Error!', msg: 'Failed to add ' + inbound.name + ' to ' + 
                          target_name + '. POST returned status: ' + status });
                       });
                }

            }
            }])
    
    // Copy a host after drag-n-drop
    .factory('CopyMoveHost', ['$compile', 'Alert', 'ProcessErrors', 'Find', 'Wait', 'Rest', 'Empty', 'GetBasePath',
        function($compile, Alert, ProcessErrors, Find, Wait, Rest, Empty, GetBasePath) {
        return function(params) {

            var scope = params.scope;
            var target = Find({ list: scope.groups, key: 'id', val: params.target_tree_id });
            var host = Find({ list: scope.hosts, key: 'id', val: params.host_id });
            
            var found = false;
            
            if (host.summary_fields.all_groups) {
                for (var i=0; i< host.summary_fields.all_groups.length; i++) {
                    if (host.summary_fields.all_groups[i].id == target.group_id) {
                       found = true;
                       break;
                    }
                }
            }
            if (found) {
                var html = '';
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
                var e = angular.element(document.getElementById('inventory-modal-container'));
                e.empty().append(html);
                $compile(e)(scope);
                
                // Display it
                $('#copy-alert-modal').modal({
                    backdrop: 'static',
                    keyboard: true,
                    show: true
                    });
                
            }
            else {
                // Build the html for our prompt dialog
                var html = '';
                html += "<div id=\"copy-prompt-modal\" class=\"modal fade\">\n";
                html += "<div class=\"modal-dialog\">\n";
                html += "<div class=\"modal-content\">\n";
                html += "<div class=\"modal-header\">\n";
                html += "<button type=\"button\" class=\"close\" data-target=\"#copy-prompt-modal\" " + 
                    "data-dismiss=\"modal\" aria-hidden=\"true\">&times;</button>\n";
                html += "<h3>Copy Host</h3>\n";
                html += "</div>\n";
                html += "<div class=\"modal-body\">\n";
                html += "<p>Are you sure you want to copy host " + host.name + ' to group ' + target.name + '?</p>';            
                html += "</div>\n";
                html += "<div class=\"modal-footer\">\n";
                html += "<a href=\"#\" data-target=\"#prompt-modal\" data-dismiss=\"modal\" class=\"btn btn-default\">No</a>\n";
                html += "<a href=\"\" data-target=\"#prompt-modal\" ng-click=\"copyHost()\" class=\"btn btn-primary\">Yes</a>\n";
                html += "</div>\n";
                html += "</div><!-- modal-content -->\n";
                html += "</div><!-- modal-dialog -->\n";
                html += "</div><!-- modal -->\n";
                
                // Inject our custom dialog
                var e = angular.element(document.getElementById('inventory-modal-container'));
                e.empty().append(html);
                $compile(e)(scope);
                
                // Display it
                $('#copy-prompt-modal').modal({
                    backdrop: 'static',
                    keyboard: true,
                    show: true
                    });

                scope.copyHost = function() {
                    $('#copy-prompt-modal').modal('hide');
                    Wait('start');
                    Rest.setUrl(GetBasePath('groups') + target.group_id + '/hosts/');
                    Rest.post(host)
                        .success(function(data, status, headers, config) {
                            // Signal the controller to refresh the hosts view
                            scope.$emit('GroupTreeRefreshed');
                            })
                        .error(function(data, status, headers, config) {
                            Wait('stop');
                            ProcessErrors(scope, data, status, null,
                                { hdr: 'Error!', msg: 'Failed to add ' + host.name + ' to ' + 
                                  target.name + '. POST returned status: ' + status });
                            });
                    }
            }
            }
            }]);
