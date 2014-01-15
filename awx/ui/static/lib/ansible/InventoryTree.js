
/************************************
 *
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  InventoryTree.js
 *
 *  Build data for the tree selector table used on inventory detail page.
 *
 */

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
    

    // Figure out the group level tool tip
    .factory('GetToolTip', [ 'FormatDate', function(FormatDate) {
        return function(params) {
            
            var node = params.node;   
      
            var tip = ''; 
            var link = '';
            var html_class = '';
            var active_failures = node.hosts_with_active_failures;
            var total_hosts = node.total_hosts;
            var source = node.summary_fields.inventory_source.source;
            var status = node.summary_fields.inventory_source.status;

            // Return values for the status indicator
            var status_date = node.summary_fields.inventory_source.last_updated
            var last_update = ( status_date == "" || status_date == null ) ? null : FormatDate(new Date(status_date));  
            
            switch (status) {
                case 'never updated':
                    html_class = 'na';
                    tip = '<p>Inventory update has not been performed.</p>';
                    link = '';
                    break;
                case 'failed':
                    tip = '<p>Inventory update failed! Click to view process output.</p>';
                    link = '/#/inventories/' + node.inventory + '/groups?name=' + node.name;
                    html_class = true;
                    break;
                case 'successful':
                    tip = '<p>Inventory update completed on ' + last_update + '.</p>';
                    html_class = false;
                    link = '';
                    break; 
                case 'updating':
                    tip = '<p>Inventory update process running now. Click to view status.</p>';
                    link = '/#/inventories/' + node.inventory + '/groups?name=' + node.name;
                    html_class = false;
                    break;
                }
            
            if (status !== 'failed' && status !== 'updating') {
                // update status will not override job status
                if (active_failures > 0) {
                    tip += "<p>Contains " + active_failures +
                        [ (active_failures == 1) ? ' host' : ' hosts' ] + ' with failed jobs. Click to view the offending ' +
                        [ (active_failures == 1) ? ' host' : ' hosts' ] + '.</p>';
                        link = '/#/inventories/' + node.inventory + '/hosts?has_active_failures=true';
                        html_class = 'true';
                }
                else {
                    if (total_hosts == 0) {
                        // no hosts
                        tip += "<p>There are no hosts in this group. It's a sad empty shell.</p>";
                        html_class = (html_class == '') ? 'na' : html_class;
                    }
                    else if (total_hosts == 1) {
                        // on host with 0 failures
                        tip += "<p>The 1 host in this group is happy! It does not have a job failure.</p>";
                        html_class = 'false';
                    } 
                    else {
                        // many hosts with 0 failures
                        tip += "<p>All " + total_hosts + " hosts in this group are happy! None of them have " + 
                            " job failures.</p>";
                        html_class = 'false';
                    }
                }
            }

            return { tooltip: tip, url: link, 'class': html_class };
      
            }
            }])


    .factory('GetInventoryToolTip', [ 'FormatDate', function(FormatDate) {
        return function(params) {
            
            var node = params.node;   
      
            var tip = ''; 
            var link = '';
            var html_class = '';
            var active_failures = node.hosts_with_active_failures;
            var total_hosts = node.total_hosts;
            var group_failures = node.groups_with_active_failures;
            var total_groups = node.total_groups; 
            var inventory_sources = node.total_inventory_sources;
      
            if (group_failures > 0) {
               tip += "Has " + group_failures +
                   [ (group_failures == 1) ? ' group' : ' groups' ] + ' with failed inventory updates. ' + 
                   'Click to view the offending ' +
                   [ (group_failures == 1) ? ' group.' : ' groups.' ];
               link = '/#/inventories/' + node.id + '/groups?status=failed';
               html_class = 'true';
            }
            else if (inventory_sources == 1) {
                // on host with 0 failures
                tip += "<p>1 group with an inventory source is happy! No updates have failed.</p>";
                link = '';
                html_class = 'false';
            }
            else if (inventory_sources > 0) {
                tip += "<p>" + inventory_sources + " groups with an inventory source are happy! No updates have failed.</p>";
                link = 0;
                html_class = 'false';
            } 

            if (html_class !== 'true') {
               // Add job status
               if (active_failures > 0) {
                  tip += "<p>Contains " + scope.inventories[i].hosts_with_active_failures +
                      [ (active_failures == 1) ? ' host' : ' hosts' ] + ' with job failures. Click to view the offending ' +
                      [ (active_failures == 1) ? ' host' : ' hosts' ] + '.</p>';
                  link = '/#/inventories/' + node.id + '/hosts?has_active_failures=true';
                  html_class = 'true';
               }
               else if (total_hosts == 0) {
                   tip += "<p>There are no hosts in this inventory. It's a sad empty shell.</p>";
                   link = "";
                   html_class = (html_class == '') ? 'na' : html_class;
               }
               else if (total_hosts == 1) {
                   tip += "<p>The 1 host found in this inventory is happy! There are no job failures.</p>";
                   link = "";
                   html_class = "false";
               }
               else if (total_hosts > 0) {
                   tip += "<p>All " + total_hosts + " hosts are happy! There are no job failures.";
                   link = "";
                   html_class = "false";
               }
            } 

            return { tooltip: tip, url: link, 'class': html_class };
      
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
                    for (var j=0; j < sorted[j].children.length; i++) {
                        children.push(sorted[j].id);
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
                        //console.log(groups);
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
    .factory('UpdateGroup', [ function() {
        return function(params) {
            
            var scope = params.scope; 
            var group_id = params.group_id; 
            var properties = params.properties;   // object of key:value pairs to update
            
            for (var i=0; i < scope.groups.length; i++) {
                if (scope.groups[i].group_id == group_id) {
                    var grp = scope.groups[i]; 
                    for (var p in properties) {
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
    .factory('CopyMoveGroup', ['$compile', 'Alert', 'ProcessErrors', 'Find', 
        function($compile, Alert, ProcessErrors, Find) {
        return function(params) {
            var scope = params.scope;
            
            var target = Find({ list: scope.groups, key: 'id', val: params.target_tree_id });
            var inbound = Find({ list: scope.groups, key: 'id', val: params.inbound_tree_id });
            
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
            html += "<div class=\"modal-body text-center\">\n";
            
            if (target.id == 1) {
                html += "<p>Are you sure you want to move group " + inbound.name + " to the top level?</p>";
            }
            else if (inbound.parent == 0) {
                html += "<p>Are you sure you want to move group " + inbound.name + " away from the top level?</p>";
            }
            else {
                html += "<p>Would you like to copy or move group <em>" + inbound.name + "</em> to group <em>" + target.name + "</em>?</p>\n";
                html += "<div style=\"margin-top: 30px;\">\n";
                html += "<a href=\"\" ng-click=\"moveGroup()\" class=\"btn btn-primary\" style=\"margin-right: 15px;\"><i class=\"fa fa-cut\"></i> Move</a>\n";
                html += "<a href=\"\" ng-click=\"copyGroup()\" class=\"btn btn-primary\"><i class=\"fa fa-copy\"></i> Copy</a>\n";
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
            e.append(html);
            $compile(e)(scope);
            
            // Display it
            $('#copy-prompt-modal').modal({
                backdrop: 'static',
                keyboard: true,
                show: true
                });
            
            // Respond to copy or move... 
            scope.moveGroup = function() {
                $('#copy-prompt-modal').modal('hide');
                console.log('moving the group...');
                }

            scope.copyGroup = function() {
                $('#copy-prompt-modal').modal('hide');
                console.log('copying the group...');
                }

            }
            }]);
