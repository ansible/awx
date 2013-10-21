
/************************************
 *
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  TreeSelector.js
 *
 */

angular.module('TreeSelector', ['Utilities', 'RestServices'])
    .factory('BuildTree', ['Rest', 'GetBasePath', 'ProcessErrors', '$compile', '$rootScope', 'Wait', 'SortNodes',
        function(Rest, GetBasePath, ProcessErrors, $compile, $rootScope, Wait, SortNodes) {
        return function(params) {

            var scope = params.scope; 
            var inventory_id = params.inventory_id;
            var emit_on_select = params.emit_on_select;
            var target_id = params.target_id;
            var refresh_tree = (params.refresh == undefined || params.refresh == false) ? false : true;

            var html = '';
            var toolTip = 'Hosts have failed jobs?';
            var idx = 0;

            function buildHTML(tree_data) {
                var sorted = SortNodes(tree_data);
                html += (sorted.length > 0) ? "<ul>\n" : "";
                for(var i=0; i < sorted.length; i++) {
                   html += "<li id=\"search-node-0" + idx + "\" data-state=\"opened\" data-hosts=\"" + sorted[i].related.hosts + "\" " +
                       "data-description=\"" + sorted[i].description + "\" " + 
                       "data-failures=\"" + sorted[i].has_active_failures + "\" " +
                       "data-groups=\"" + sorted[i].related.groups + "\" " + 
                       "data-name=\"" + sorted[i].name + "\" " +
                       "data-group-id=\"" + sorted[i].id + "\" " + 
                       "><div class=\"expand-container\"><a href=\"\" class=\"expand\"><i class=\"icon-caret-down\"></i></a></div> " +
                       "<div class=\"badge-container\"><i class=\"field-badge icon-failures-" + sorted[i].has_active_failures + "\" " +
                       "aw-tool-tip=\"" + toolTip + "\" data-placement=\"top\"></i></div> " +
                       "<div class=\"title-container\"><a href=\"\" class=\"activate\">" + sorted[i].name + "</a></div>";
                   idx++;
                   if (sorted[i].children.length > 0) {
                      buildHTML(sorted[i].children);
                   }
                   else {
                      html += "</li>\n";
                   }
                }
                html += "</ul>\n";  
            }

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
                elm.addClass('active');
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
                   if (childlists && childlists.length > 0) {
                      // has childen
                      for (var i=0; i < childlists.length; i++) {
                          angular.element(childlists[i]).addClass('hidden');
                      }
                   }
                   /* When the active node's parent is closed, activate the parent */
                   if ($(parent).find('.active').length > 0) {
                      $(parent).find('.active').removeClass('active');
                      sibling.addClass('active');
                      refresh(parent);
                   }
                }
                }

            // The HTML is ready. Insert it into the view.
            if (scope.searchTreeReadyRemove) {
               scope.searchTreeReadyRemove();
            }
            scope.searchTreeReadyRemove = scope.$on('searchTreeReady', function(e, html) {
                var container = angular.element(document.getElementById(target_id));
                container.empty();
                var compiled = $compile(html)(scope);
                container.append(compiled);
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
                 
                // Attempt to stop the title from dropping to the next 
                // line
                $(container).find('.title-container').each(function(idx) {
                    var parent = $(this).parent();
                    if ($(this).width() >= parent.width()) {
                       $(this).css('width','80%');
                    } 
                    });

                Wait('stop');
                });
            
            // Build the HTML for our tree
            if (scope.buildAllGroupsRemove) {
               scope.buildAllGroupsRemove();
            }
            scope.buildAllGroupsRemove = scope.$on('buildAllGroups', function(e, inventory_name, inventory_tree) {
                Rest.setUrl(inventory_tree);
                Rest.get()
                    .success( function(data, status, headers, config) {
                        buildHTML(data);
                        scope.$emit('searchTreeReady', html + "</li>\n</ul>\n");
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

            Wait('start');

            // Load the inventory root node
            Rest.setUrl (GetBasePath('inventory') + inventory_id + '/');
            Rest.get()
                 .success( function(data, status, headers, config) {
                     html += "<div class=\"title\">Group Selector:</div>\n" +
                       "<ul id=\"inventory-tree\" class=\"tree-root\">\n" +
                       "<li id=\"inventory-root-node\" data-state=\"opened\" data-hosts=\"" + data.related.hosts + "\" " +
                       "data-description=\"" + data.description + "\" " + 
                       "data-failures=\"" + data.has_active_failures + "\" " +
                       "data-groups=\"" + data.related.groups + "\" " + 
                       "data-name=\"" + data.name + "\" " +
                       ">" +
                       "<i class=\"icon-sitemap\"></i> " +
                       "<a href=\"\" class=\"activate active\">" + data.name + "</a>";
                     
                     scope.$emit('buildAllGroups', data.name, data.related.tree, data.related.groups);
                     
                     if (!refresh_tree) {
                        // if caller requests refresh, let caller handle next steps / node selection
                        scope.$emit(emit_on_select, 'inventory-root-node', null, 'All Hosts');
                     }

                     })
                 .error( function(data, status, headers, config) {
                     ProcessErrors(scope, data, status, null,
                         { hdr: 'Error!', msg: 'Failed to get inventory: ' + inventory_id + '. GET returned: ' + status });
                     });
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
            }]);




