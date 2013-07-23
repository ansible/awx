/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  InventoryHelper
 *  Routines for building the tree. Everything related to the tree is here except
 *  for the menu piece. The routine for building the menu is in InventoriesEdit controller
 *  (controllers/Inventories.js)
 *  
 */
 
angular.module('InventoryHelper', [ 'RestServices', 'Utilities', 'OrganizationListDefinition',
                                    'SearchHelper', 'PaginateHelper', 'ListGenerator', 'AuthService',
                                    'InventoryHelper', 'RelatedSearchHelper', 'RelatedPaginateHelper',
                                    'InventoryFormDefinition'
                                    ]) 

    .factory('LoadTreeData', ['Alert', 'Rest', 'Authorization', '$http',
    function(Alert, Rest, Authorization, $http) {
    return function(params) {

        var scope = params.scope;
        var inventory = params.inventory;
        var groups = inventory.related.root_groups;
        var hosts = inventory.related.hosts; 
        var inventory_name = inventory.name; 
        var inventory_url = inventory.url;
        var inventory_id = inventory.id;
        var has_active_failures = inventory.has_active_failures;
        var inventory_descr = inventory.description;
        var idx=0;
        var treeData = [];

        // Ater inventory top-level hosts, load top-level groups
        if (scope.HostLoadedRemove) {
            scope.HostLoadedRemove();
        }
        scope.HostLoadedRemove = scope.$on('hostsLoaded', function() {
            var filter = (scope.inventoryFailureFilter) ? "has_active_failures__int=1&" : ""; 
            var url = groups + '?' + filter + 'order_by=name';
            Rest.setUrl(url);
            Rest.get()
                .success( function(data, status, headers, config) {    
                    for (var i=0; i < data.results.length; i++) {
                        treeData[0].children.push({
                           data: {
                               title: data.results[i].name
                               },
                           attr: {
                               id: idx,
                               group_id: data.results[i].id,
                               type: 'group',
                               name: data.results[i].name, 
                               description: data.results[i].description,
                               inventory: data.results[i].inventory,
                               all: data.results[i].related.all_hosts,
                               children: data.results[i].related.children,
                               hosts: data.results[i].related.hosts,
                               variable: data.results[i].related.variable_data,
                               "data-failures": data.results[i].has_active_failures
                               },
                           state: 'closed'
                           });
                        idx++;
                    }
                    scope.$emit('buildTree', treeData, idx);
                    })
                .error( function(data, status, headers, config) {
                    Alert('Error', 'Failed to laod tree data. Url: ' + groups + ' GET status: ' + status);
                    });
            });

        // Setup tree_data
        Rest.setUrl(hosts + '?order_by=name'); 
        Rest.get()
            .success ( function(data, status, headers, config) {
                treeData =
                    [{ 
                    data: {
                        title: inventory_name
                        }, 
                    attr: {
                        type: 'inventory',
                        id: 'inventory-node',
                        url: inventory_url,
                        'inventory_id': inventory_id,
                        hosts: hosts,
                        name: inventory_name,
                        description: inventory_descr,
                        "data-failures": inventory.has_active_failures
                        },
                    state: 'open',
                    children:[] 
                    }];
                scope.$emit('hostsLoaded');
            })
            .error ( function(data, status, headers, config) {
                Alert('Error', 'Failed to laod tree data. Url: ' + hosts + ' GET status: ' + status);
            });
        }
        }])


    .factory('TreeInit', ['Alert', 'Rest', 'Authorization', '$http', 'LoadTreeData',
    function(Alert, Rest, Authorization, $http, LoadTreeData) {
    return function(params) {

        var scope = params.scope;
        var inventory = params.inventory;
        var groups = inventory.related.root_groups;
        var hosts = inventory.related.hosts; 
        var inventory_name = inventory.name; 
        var inventory_url = inventory.url;
        var inventory_id = inventory.id;
        var inventory_descr = inventory.description;
        var tree_id = '#tree-view';
        
        // After loading the Inventory top-level data, initialize the tree
        if (scope.buildTreeRemove) {
           scope.buildTreeRemove();
        }
        scope.buildTreeRemove = scope.$on('buildTree', function(e, treeData, index) {
            var idx = index;
            $(tree_id).jstree({
                "core": { "initially_open":['inventory-node'] },
                "plugins": ['themes', 'json_data', 'ui', 'contextmenu'],
                "themes": {
                    "theme": "ansible",
                    "dots": false,
                    "icons": true
                    },
                "ui": { "initially_select": [ 'inventory-node' ]},
                "json_data": {
                    data: treeData,
                    ajax: {
                        url: function(node){
                            scope.selected_node = node;
                            return $(node).attr('children');
                            },
                        headers: { 'Authorization': 'Token ' + Authorization.getToken() },
                        success: function(data) {
                            var response = [];
                            var filter = (scope.inventoryFailureFilter) ? "has_active_failures__int=1&" : ""; 
                            for (var i=0; i < data.results.length; i++) {
                                response.push({
                                    data: {
                                       title: data.results[i].name
                                       },
                                    attr: {
                                       id: idx,
                                       group_id: data.results[i].id,
                                       type: 'group',
                                       name: data.results[i].name, 
                                       description: data.results[i].description,
                                       inventory: data.results[i].inventory,
                                       all: data.results[i].related.all_hosts,
                                       children: data.results[i].related.children + '?' + filter + 'order_by=name',
                                       hosts: data.results[i].related.hosts,
                                       variable: data.results[i].related.variable_data,
                                       "data-failures": data.results[i].has_active_failures
                                       },
                                    state: 'closed'
                                    });
                                idx++;
                            }
                            return response;
                            }
                        }
                    },
                "contextmenu": {
                    items: scope.treeController
                    }
                });
  
            $(tree_id).bind("loaded.jstree", function () {
                scope.$emit('treeLoaded');
                });
            
            // When user clicks on a group, display the related hosts in the list view
            $(tree_id).bind("select_node.jstree", function(e, data){
                //selected node object: data.inst.get_json()[0];
                //selected node text: data.inst.get_json()[0].data
                scope.$emit('NodeSelect',data.inst.get_json()[0]);
                });
            });
   
        LoadTreeData(params);
        
        }
        }])


    .factory('LoadInventory', ['$routeParams', 'Alert', 'Rest', 'Authorization', '$http', 'ProcessErrors',
        'RelatedSearchInit', 'RelatedPaginateInit', 'GetBasePath', 'LoadBreadCrumbs', 'InventoryForm',
    function($routeParams, Alert, Rest, Authorization, $http, ProcessErrors, RelatedSearchInit, RelatedPaginateInit,
        GetBasePath, LoadBreadCrumbs, InventoryForm) {
    return function(params) {
        
        // Load inventory detail record
        
        var scope = params.scope;
        var form = InventoryForm;
        scope.relatedSets = [];
        scope.master = {};

        Rest.setUrl(GetBasePath('inventory') + $routeParams.id + '/');
        Rest.get()
            .success( function(data, status, headers, config) {
                LoadBreadCrumbs({ path: '/inventories/' + $routeParams.id, title: data.name });
                for (var fld in form.fields) {
                  if (form.fields[fld].realName) {
                     if (data[form.fields[fld].realName]) {
                        scope[fld] = data[form.fields[fld].realName];
                        scope.master[fld] = scope[fld];
                     }
                  }
                  else {
                     if (data[fld]) {
                        scope[fld] = data[fld];
                        scope.master[fld] = scope[fld];
                     }
                  }
                  if (form.fields[fld].type == 'lookup' && data.summary_fields[form.fields[fld].sourceModel]) {
                      scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] = 
                          data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                      scope.master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                          scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField];
                  }
                }

                // Load the tree view
                scope.TreeParams = { scope: scope, inventory: data };
                scope.variable_url = data.related.variable_data;
                scope.relatedSets['hosts'] = { url: data.related.hosts, iterator: 'host' };
                RelatedSearchInit({ scope: scope, form: form, relatedSets: scope.relatedSets });
                RelatedPaginateInit({ scope: scope, relatedSets: scope.relatedSets });
                scope.$emit('inventoryLoaded');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve inventory: ' + $routeParams.id + '. GET status: ' + status });
                });

        }
        }])

    .factory('RefreshGroupName', [ function() {
    return function(node, name, description) {
        // Call after GroupsEdit controller saves changes
        $('#tree-view').jstree('rename_node', node, name);
        node.attr('description', description);
        }
        }])

    .factory('RefreshTree', ['Alert', 'Rest', 'Authorization', '$http', 'TreeInit', 'LoadInventory',
    function(Alert, Rest, Authorization, $http, TreeInit, LoadInventory) {
    return function(params) {

        // Call after an Edit or Add to refresh tree data
      
        var scope = params.scope;
        var openId = [];
        var selectedId;

        if (scope.treeLoadedRemove) {
           scope.treeLoadedRemove();
        }
        scope.treeLoadedRemove = scope.$on('treeLoaded', function() {
            // Called recursively to pop the next openId node value and open it. 
            // Opens the list in reverse so that nodes open in parent then child order,
            // drilling down to the last selected node.
            var id, node;
            if (openId.length > 0) {
               id = openId.pop();
               node = $('#tree-view li[id="' + id + '"]');
               $.jstree._reference('#tree-view').open_node(node, function(){ scope.$emit('treeLoaded'); }, true);
            }
            else {
               if (selectedId !== null && selectedId !== undefined) {
                  // Click on the previously selected node
                  $('#tree-view li[id="' + selectedId + '"] a').first().click();
               }
            }
            });

        if (scope.inventoryLoadedRemove) {
           scope.inventoryLoadedRemove();
        }
        scope.inventoryLoadedRemove = scope.$on('inventoryLoaded', function() {
            // Get the list of open tree nodes starting with the current group and going up 
            // the tree until we hit the inventory or root node.
            function findOpenNodes(node) {
                if (node.attr('id') != 'inventory-node') {
                   if (node.prop('tagName') == 'LI' && (node.hasClass('jstree-open') || node.find('.jstree-clicked'))) {
                      openId.push(node.attr('id'));
                   }
                   findOpenNodes(node.parent());
                }
            }
            selectedId = scope.selectedNode.attr('id');
            findOpenNodes(scope.selectedNode);
            $('#tree-view').jstree('destroy');
            TreeInit(scope.TreeParams);        
            });

        LoadInventory({ scope: scope });
        
        }
        }]);

