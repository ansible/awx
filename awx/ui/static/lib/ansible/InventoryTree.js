
/************************************
 *
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  InventoryTree.js
 *
 *  Build data for the tree selector table used on inventory detail page.
 *
 */

angular.module('InventoryTree', ['Utilities', 'RestServices', 'GroupsHelper'])
    
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

    .factory('BuildTree', ['Rest', 'GetBasePath', 'ProcessErrors', 'SortNodes', 'Wait', 'UpdateStatusMsg', 
        function(Rest, GetBasePath, ProcessErrors, SortNodes, Wait, UpdateStatusMsg) {
        return function(params) {
            
            var inventory_id = params.inventory_id;
            var scope = params.scope;
            //var selected_id = params.

            var groups = [];
            var id = 0;

            function buildGroups(tree_data, parent, level) {
                var sorted = SortNodes(tree_data);
                for (var i=0; i < sorted.length; i++) {
                    var currentId = id;
                    var stat = UpdateStatusMsg({ status: sorted[i].summary_fields.inventory_source.status });
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
                       group_id: sorted[i].id,
                       event_level: level,
                       ngicon: (sorted[i].children.length > 0) ? 'icon-collapse-alt' : null,
                       related: { children: (sorted[i].children.length > 0) ? sorted[i].related.children : '' },
                       status: sorted[i].summary_fields.inventory_source.status,
                       status_badge_class: stat['class'],
                       status_badge_tooltip: stat['tooltip'],
                       selected_class: ''
                       }
                    groups.push(group);
                    id++;
                    if (sorted[i].children.length > 0) {
                        buildGroups(sorted[i].children, currentId, level + 1);
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
                        buildGroups(data, 0, 0);
                        scope.$emit('searchTreeReady', inventory_name, groups);
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

    .factory('ClickNode', [ function() {
        return function(params) {
            var selector = params.selector;   //jquery selector string to find the correct <li>
            $(selector + ' .activate').first().click();
            }
            }])

    .factory('DeleteNode', [ function() {
        return function(params) {
            var selector = params.selector;   //jquery selector string to find the correct <li>
            $(selector).first().detach();
            }
            }]);