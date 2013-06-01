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
                                    'SearchHelper', 'PaginateHelper', 'ListGenerator', 'AuthService'
                                    ]) 

    .factory('TreeInit', ['Alert', 'Rest', 'Authorization', '$http',
    function(Alert, Rest, Authorization, $http) {
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
        var idx=0;
        var treeData = [];

        // After loading the Inventory top-level data, initialize the tree
        if (scope.buildTreeRemove) {
           scope.buildTreeRemove();
        }
        scope.buildTreeRemove = scope.$on('buildTree', function() {
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
                                       children: data.results[i].related.children + '?order_by=name',
                                       hosts: data.results[i].related.hosts,
                                       variable: data.results[i].related.variable_data
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
            
            // When user clicks on a group, display the related hosts in the list view
            $(tree_id).bind("select_node.jstree", function(evt, data){
                //selected node object: data.inst.get_json()[0];
                //selected node text: data.inst.get_json()[0].data
                scope.$emit('NodeSelect',data.inst.get_json()[0]);
                });
            });
        
        // Ater inventory top-level hosts, load top-level groups
        if (scope.HostLoadedRemove) {
            scope.HostLoadedRemove();
        }
        scope.HostLoadedRemove = scope.$on('hostsLoaded', function() {
            Rest.setUrl(groups + '?order_by=name');
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
                               variable: data.results[i].related.variable_data
                               },
                           state: 'closed'
                           });
                        idx++;
                    }
                    scope.$emit('buildTree');
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
                        description: inventory_descr
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
        }]);
