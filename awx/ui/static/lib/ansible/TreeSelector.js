
/************************************
 *
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  TreeSelector.js
 *
 */

angular.module('TreeSelector', ['Utilities', 'RestServices', 'TreeSelector', 'GroupsHelper'])
    
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

    .factory('BuildTree', ['Rest', 'GetBasePath', 'ProcessErrors', '$compile', '$rootScope', 'Wait', 'SortNodes', 'GetToolTip',
        'GetInventoryToolTip',
        function(Rest, GetBasePath, ProcessErrors, $compile, $rootScope, Wait, SortNodes, GetToolTip, GetInventoryToolTip) {
        return function(params) {
            var scope = params.scope; 
            var inventory_id = params.inventory_id;
            var emit_on_select = params.emit_on_select;
            var target_id = params.target_id;
            var refresh_tree = (params.refresh == undefined || params.refresh == false) ? false : true;
            var moveable = (params.moveable == undefined || params.moveable == false) ? false : true;
            var group_id = params.group_id;
            var id = params.id;

            var html = '';
            var toolTip = 'Hosts have failed jobs?';
            var idx = 0;

            function refresh(parent) {
                var group, title;
                var id = parent.attr('id');
                if (parent.attr('data-group-id')) {
                   group = parent.attr('data-group-id');
                   title = parent.attr('data-name');
                }
                else {
                   group = null;
                   title = 'All Hosts'
                }
                // The following will trigger the host list to load. See Inventory.js controller.
                scope.$emit(emit_on_select, id, group, title);
                }
                
            function activate(e) {
                /* Set the clicked node as active */
                var elm = angular.element(e.target);  //<a>
                var parent = angular.element(e.target.parentNode.parentNode); //<li>
                $('.search-tree .active').removeClass('active');
                elm.parent().addClass('active');  // add active class to <div>
                refresh(parent);
                }

            function toggle(e) {      
                var id, parent, elm, icon;

                if (e.target.tagName == 'I') {
                   id = e.target.parentNode.parentNode.parentNode.attributes.id.value;
                   parent = angular.element(e.target.parentNode.parentNode.parentNode);  //<li>
                   elm = angular.element(e.target.parentNode);  // <a>
                }
                else {
                   id = e.target.parentNode.parentNode.attributes.id.value;
                   parent = angular.element(e.target.parentNode.parentNode);
                   elm = angular.element(e.target);
                }

                var sibling = angular.element(parent.children()[2]); // <a>
                var state = parent.attr('data-state');
                var icon = angular.element(elm.children()[0]);

                if (state == 'closed') {
                   // expand the elment
                   var childlists = parent.find('ul');
                   if (childlists && childlists.length > 0) {
                      // has childen
                      for (var i=0; i < childlists.length; i++) {
                          var listChild = angular.element(childlists[i]);
                          var listParent = angular.element(listChild.parent());
                          if (listParent.attr('id') == id) {
                             angular.element(childlists[i]).removeClass('hidden');
                          }
                      }
                   }
                   parent.attr('data-state','open'); 
                   icon.removeClass('icon-caret-right').addClass('icon-caret-down');
                }
                else {
                   // close the element
                   parent.attr('data-state','closed'); 
                   icon.removeClass('icon-caret-down').addClass('icon-caret-right');
                   var childlists = parent.find('ul');
                   var sublist, subicon;
                   if (childlists && childlists.length > 0) {
                      // has childen
                      childlists.each(function(idx) {
                          $(this).addClass('hidden');
                          subicon = $(this).find('li').first().find('.expand-container i');
                          subicon.removeClass('icon-caret-down').addClass('icon-caret-right');
                      });
                   }
                   /* When the active node's parent is closed, activate the parent */
                   if ($(parent).find('.active').length > 0) {
                      $(parent).find('.active').removeClass('active');
                      sibling.addClass('active');
                      refresh(parent);
                   }
                }
                }

            if (scope.moveNodeRemove) {
               scope.moveNodeRemove();
            }
            scope.moveNodeRemove = scope.$on('MoveNode', function(e, node, parent, target) {
                var inv_id = scope['inventory_id'];
                var variables;

                function cleanUp(state) {
                    /*
                    if (state !== 'fail') {
                        // Visually move the element. Elment will be appended to the
                        // end of target element list
                        var elm = $('#' + node.attr('id')).detach();
                        if (target.find('ul').length > 0) {
                           // parent has children
                           target.find('ul').first().append(elm);
                        }
                        else {
                           target.append('<ul></ul>');
                           target.find('ul').first().append(elm);
                        }
                        
                        // Remove any styling that might be left on the target 
                        // and put the expander icon back the way it should be
                        target.find('div').each(function(idx) {
                            if (idx > 0 && idx < 3) {
                               $(this).css({ 'border-bottom': '2px solid #f5f5f5' });
                            }
                            });
                        
                        // Make sure the parent and target have the correct expander class/icon.
                        function setExpander(n) {
                            var c = n.find('.expand-container');
                            var icon;
                            c.first().empty();
                            if (n.attr('id') == 'inventory-root-node') {
                               c.first().html('<i class=\"icon-sitemap\"></i>');
                            }
                            else if (c.length > 1) {
                               // not root and has children, put expander icon back
                               icon = (n.attr('data-state') == 'opened') ? 'icon-caret-down' : 'icon-caret-right';
                               c.first().html('<a class="expand"><i class="' + icon + '"></i></a>');
                               c.first().find('a').first().bind('click', toggle);
                            }
                            }
                        setExpander(target);
                        setExpander(parent);
                    }
                    Wait('stop');
                    */
                    // Reload the tree
                    html = '';
                    idx = 0;
                    loadTreeData();
                    }

                // disassociate the group from the original parent
                if (scope.removeGroupRemove) {
                   scope.removeGroupRemove(); 
                }
                scope.removeGroupRemove = scope.$on('removeGroup', function() {
                    if (parent.attr('data-group-id')) {
                        // Only remove a group from a parent when the parent is a group and not the inventory root
                        var url = GetBasePath('base') + 'groups/' + parent.attr('data-group-id') + '/children/';
                        Rest.setUrl(url);
                        Rest.post({ id: node.attr('data-group-id'), disassociate: 1 })
                            .success( function(data, status, headers, config) {
                                cleanUp('success');
                                })
                            .error( function(data, status, headers, config) {
                                cleanUp('fail');
                                ProcessErrors(scope, data, status, null,
                                    { hdr: 'Error!', msg: 'Failed to remove ' + node.attr('name') + ' from ' + 
                                      parent.attr('name') + '. POST returned status: ' + status });
                                });
                    }
                    else {
                        cleanUp('success');
                    }
                    });

                if (scope['addToTargetRemove']) {
                   scope.addToTargetRemove();
                }
                scope.addToTargetRemove = scope.$on('addToTarget', function() {
                   // add the new group to the target parent
                   var url = (target.attr('data-group-id')) ? GetBasePath('base') + 'groups/' + target.attr('data-group-id') + '/children/' :
                       GetBasePath('inventory') + inv_id + '/groups/';
                   var group = { 
                       id: node.attr('data-group-id'),
                       name: node.attr('data-name'),
                       description: node.attr('data-description'),
                       inventory: inv_id
                       }
                   Rest.setUrl(url);
                   Rest.post(group)
                       .success( function(data, status, headers, config) {
                           scope.$emit('removeGroup');
                           })
                       .error( function(data, status, headers, config) {
                           cleanUp('fail');
                           ProcessErrors(scope, data, status, null,
                              { hdr: 'Error!', msg: 'Failed to add ' + node.attr('name') + ' to ' + 
                              target.attr('name') + '. POST returned status: ' + status });
                           });
                   });

                Wait('start');
                // Lookup the inventory. We already have what we need except for variables.
                var url = GetBasePath('base') + 'groups/' + node.attr('data-group-id') + '/';
                Rest.setUrl(url);
                Rest.get()
                    .success( function(data, status, headers, config) {
                        variables = (data.variables) ? JSON.parse(data.variables) : "";
                        scope.$emit('addToTarget');
                        })
                    .error( function(data, status, headers, config) {
                        cleanUp('fail');
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Failed to lookup group ' + node.attr('name') + 
                            '. GET returned status: ' + status });
                        });
                });

            // The HTML is ready. Insert it into the view.
            if (scope.searchTreeReadyRemove) {
               scope.searchTreeReadyRemove();
            }
            scope.searchTreeReadyRemove = scope.$on('searchTreeReady', function(e, html) {
                
                var container = angular.element(document.getElementById(target_id));
                container.empty();
                var compiled = $compile(html)(scope);
                container.append(compiled);
                
                function setTitleWidth(elm) {
                    // Fix for overflowing title text
                    var container = $('#search-tree-target');
                    var container_offset = container.offset();
                    var parent = elm.parent(); // <li>
                    var parent_offset = parent.offset();
                    var expander = parent.find('.expand-container').first();
                    var badge = parent.find('.badge-container').first(); 
                    var width = container.width() - parent_offset.left + container_offset.left - 
                        badge.width() - expander.width() - 10;
                    elm.css('width', width + 'px');
                    }

                // Fix overflowing title text now
                $('#' + target_id).find('.title-container').each(function(idx) {
                    setTitleWidth($(this));
                    });
                
                // Fix overflowing title text on screen resize
                var timeout;
                $(window).resize(function() {
                    clearTimeout(timeout); //remove prior timer so we don't resize a million times
                    timeout = setTimeout(function() {
                        $('#' + target_id).find('.title-container').each(function(idx) {
                            setTitleWidth($(this));
                            });
                        }, 500);
                    });

                var links = container.find('a');
                for (var i=0; i < links.length; i++) {
                    var link = angular.element(links[i]);
                    if (link.hasClass('expand')) {
                       link.unbind('click', toggle);
                       link.bind('click', toggle);
                    }
                    if (link.hasClass('activate')) {
                       link.unbind('click', activate);
                       link.bind('click', activate);
                    }
                }

                if (refresh_tree && group_id !== undefined) {
                   // pick a node by group_id
                   $('li[data-group-id="' + group_id + '"] .activate').first().click();
                }
                else if (refresh_tree && id !== undefined) {
                   // pick a node by id
                   $('#' + id + ' .activate').first().click();
                }
                else if (!refresh_tree) {
                   // default to the root node
                   $('#inventory-root-node .activate').first().click();
                }
                
                // Make the tree drag-n-droppable
                if (moveable) {
                    $('#selector-tree .activate').draggable({
                        cursor: "pointer",
                        cursorAt: { top: -16, left: -10 },
                        revert: 'invalid',
                        helper: 'clone',
                        start: function (e, ui) {
                            var txt = '[ ' + ui.helper.text() + ' ]';
                            ui.helper.css({ 'display': 'inline-block', 'font-weight': 'normal', 'color': '#171717', 
                                'background-color': '#f5f5f5', 'overflow': 'visible', 'white-space': 'normal',
                                'z-index': 5000 }).text(txt);
                            }
                        })
                        .droppable({
                            //hoverClass: 'droppable-hover',
                            tolerance: 'pointer',
                            over: function (e, ui) {
                                var p = $(this).parent().parent(); 
                                p.find('div').each(function(idx) {
                                    if (idx > 0 && idx < 3) {
                                       $(this).css({ 'border-bottom': '2px solid #171717' });
                                    }
                                });
                                var c = p.find('.expand-container').first();
                                c.empty().html('<i class="icon-circle-arrow-right" style="color: #171717;"></i>');
                                },
                            out: function (e, ui) {
                                var p = $(this).parent().parent();
                                p.find('div').each(function(idx) {
                                    if (idx > 0 && idx < 3) {
                                       $(this).css({ 'border-bottom': '2px solid #f5f5f5' });
                                    }
                                    });
                                var c = p.find('.expand-container');
                                var icon;
                                c.first().empty();
                                if (c.length > 1) {
                                   // has children, put expander icon back
                                   icon = (p.attr('data-state') == 'opened') ? 'icon-caret-down' : 'icon-caret-right';
                                   c.first().html('<a class="expand"><i class="' + icon + '"></i></a>');
                                   c.first().find('a').first().bind('click', toggle);
                                }
                                },
                            drop: function (e,ui) {
                                var variables;
                                var node = ui.draggable.parent().parent();    // node being moved
                                var parent = node.parent().parent();          // node from
                                var target = $(this).parent().parent();       // node to
                                scope.$emit('MoveNode', node, parent, target);
                                
                                // Make sure angular picks up changes and jQuery doesn't
                                // leave us in limbo... 
                                if (!scope.$$phase) {
                                   scope.$digest();
                                }
                                e.preventDefault(); 
                                }
                            });
                } // if moveable

                Wait('stop');
                });

            function buildHTML(tree_data) {
                var sorted = SortNodes(tree_data);
                var toolTip;

                html += (sorted.length > 0) ? "<ul>\n" : "";
                for(var i=0; i < sorted.length; i++) {
                   html += "<li id=\"search-node-0" + idx + "\" data-state=\"opened\" data-hosts=\"" + sorted[i].related.hosts + "\" " +
                       "data-description=\"" + sorted[i].description + "\" " + 
                       "data-failures=\"" + sorted[i].has_active_failures + "\" " +
                       "data-groups=\"" + sorted[i].related.groups + "\" " + 
                       "data-name=\"" + sorted[i].name + "\" " +
                       "data-group-id=\"" + sorted[i].id + "\" " + 
                       "><div class=\"expand-container\">"; 

                   if (sorted[i].children.length > 0) {
                      html += "<a href=\"\" class=\"expand\"><i class=\"icon-caret-down\"></i></a>";
                   }
                   else { 
                      html += " ";
                   }
                   html += "</div>";

                   toolTip = GetToolTip({ node: sorted[i] });

                   html += "<div class=\"badge-container\">";
                   html += "<a aw-tool-tip=\"" + toolTip.tooltip + "\" data-placement=\"top\"";
                   html += (toolTip.url !== '') ? " href=\"" + toolTip.url + "\"": ""; 
                   html += ">"; 
                   html += "<i class=\"field-badge icon-failures-" + toolTip['class'] + "\" ></i>";
                   html += "</a>";
                   html += "</div> ";

                   html += "<div class=\"title-container\"><a class=\"activate\">" + sorted[i].name + "</a></div>";
                   
                   idx++;
                   if (sorted[i].children.length > 0) {
                      buildHTML(sorted[i].children);
                   }
                   else {
                      //html += "<ul></ul>\n";
                      html += "</li>\n";
                   }
                }
                html += "</ul>\n";  
                }

            // Build the HTML for our tree
            if (scope.buildAllGroupsRemove) {
               scope.buildAllGroupsRemove();
            }
            scope.buildAllGroupsRemove = scope.$on('buildAllGroups', function(e, inventory_name, inventory_tree) {
                Rest.setUrl(inventory_tree);
                Rest.get()
                    .success( function(data, status, headers, config) {
                        buildHTML(data);
                        scope.$emit('searchTreeReady', html + "</li>\n</ul>\n</div>\n");
                        })
                    .error( function(data, status, headers, config) {
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Failed to get inventory tree for: ' + inventory_id + '. GET returned: ' + status });
                        });
                });
            
            // Builds scope.inventory_groups, used by the group picker on Hosts view to build the list of potential groups
            // that can be added to a host.  <<<< Should probably be moved to /helpers/Hosts.js
            if (scope.buildGroupListRemove) {
               scope.buildGroupListRemove();
            }
            scope.buildGroupListRemove = scope.$on('buildAllGroups', function(e, inventory_name, inventory_tree, groups_url) {
                scope.inventory_groups = [];
                Rest.setUrl(groups_url);
                Rest.get()
                    .success( function(data, status, headers, config) {
                        var groups = [];
                        for (var i=0; i < data.results.length; i++) {
                            groups.push({
                                id: data.results[i].id,
                                description: data.results[i].description, 
                                name: data.results[i].name }); 
                        }
                        scope.inventory_groups = SortNodes(groups);
                    })
                    .error( function(data, status, headers, config) { 
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Failed to get groups for inventory: ' + inventory_id + '. GET returned: ' + status });
                    });
                });

           
            function loadTreeData() {
                // Load the inventory root node
                Wait('start');
                Rest.setUrl (GetBasePath('inventory') + inventory_id + '/');
                Rest.get()
                    .success( function(data, status, headers, config) {
                        
                        var tip = GetInventoryToolTip({ node: data });
                        
                        html += "<div class=\"title\">Group Selector:</div>\n" +
                            "<div id=\"selector-tree\">\n" +
                            "<ul id=\"inventory-tree\" class=\"tree-root\">\n" +
                            "<li id=\"inventory-root-node\" data-state=\"opened\" data-hosts=\"" + data.related.hosts + "\" " +
                            "data-description=\"" + data.description + "\" " + 
                            "data-failures=\"" + data.has_active_failures + "\" " +
                            "data-groups=\"" + data.related.groups + "\" " + 
                            "data-name=\"" + data.name + "\" " +
                            "data-inventory=\"" + data.id + "\"" +
                            ">" +
                            "<div class=\"expand-container\" id=\"root-expand-container\"><i class=\"icon-sitemap\"></i></div>" +
                            "<div class=\"badge-container\" id=\"root-badge-container\">\n"; 
                        
                        html += "<a aw-tool-tip=\"" + tip['tooltip'] + "\" data-placement=\"top\"";
                        html += (tip.link) ? " href=\"" + tip['link'] + "\"" : ""; 
                        html += ">";
                        html += "<i class=\"field-badge icon-failures-" + tip['class'] + "\"></i></a>";
                        html += "</div>\n";

                        html += "<div class=\"title-container\" id=\"root-title-container\">" +
                            "<a class=\"activate\">" + data.name + "</a></div>";
                         
                        scope.$emit('buildAllGroups', data.name, data.related.tree, data.related.groups);
                         
                        })
                    .error( function(data, status, headers, config) {
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Failed to get inventory: ' + inventory_id + '. GET returned: ' + status });
                        });
                }

            loadTreeData();

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
