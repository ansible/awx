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
        var tree_id = '#tree-view';
        
        var treeData = [];

        
        // On group expand, fetch and add hosts
        if (scope.loadHostsRemove) {
           scope.loadHostsRemove();
        }
        scope.loadHostsRemove = scope.$on('loadHosts', function(){
            var node = scope.selected_node; 
            var url = $(node).attr('hosts');
            var children = [];
            // Rest and $http refuse to work. Seems we've hit a nesting limit at this point? 
            $.ajax({
                url: url, 
                dataType: 'json', 
                headers: { 'Authorization': 'Token ' + Authorization.getToken() }
                }).done( function(data) { 
                    for (var i=0; i < data.results.length; i++) {
                        // Add each host to the group node
                        $(tree_id).jstree("create_node", node, "inside", {
                            data: {
                                title: data.results[i].name, 
                                icon: '/'
                                },
                            attr: {
                                id: data.results[i].id,
                                type: 'host',
                                name: data.results[i].name, 
                                description: data.results[i].description,
                                url: data.results[i].url, 
                                variable_data: data.results[i].varaible_data,
                                inventory: data.results[i].related.inventory,
                                job_events: data.results[i].related.job_events
                                }
                            });    
                    }
                    // Open the group node
                    $(tree_id).jstree("open_node", node);  
                    });            
            });
       
        // After loading the Inventory top-level data, initialize the tree
        if (scope.buildTreeRemove) {
           scope.buildTreeRemove();
        }
        scope.buildTreeRemove = scope.$on('buildTree', function() {
            $(tree_id).jstree({
                "core": { "initially_open":['inventory-node'] },
                "plugins": ['themes', 'json_data', 'ui', 'contextmenu'],
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
                                       id: data.results[i].id,
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
                            }
                            scope.$emit('loadHosts');
                            return response;
                            }
                        }
                    },
                "contextmenu": {
                    items: scope.treeController
                    }
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
                               id: data.results[i].id,
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
                    }
                    scope.$emit('buildTree');
                    })
                .error( function(data, status, headers, config) {
                    Alert('Error', 'Failed to laod tree data. Url: ' + groups + ' GET status: ' + status);
                    });
            });

        // Load inventory all hosts
        Rest.setUrl(hosts + '?order_by=name'); 
        Rest.get()
            .success ( function(data, status, headers, config) {
                treeData = [];
                treeData.push({ 
                    data: {
                        title: inventory_name
                        }, 
                    attr: {
                        type: 'inventory',
                        id: 'inventory-node',
                        url: inventory_url,
                        'inventory_id': inventory_id,
                        name: inventory_name
                        },
                    state: 'open',
                    children:[] 
                    });
                //treeData[0].children.push({
                var all_hosts_node = {
                    data: {
                        title: 'All Hosts'
                        },
                    attr: {
                        type: 'all-hosts-group',
                        id: 'all-hosts-group',
                        url: hosts + '?order_by=name',
                        name: 'All Hosts'
                        },
                    state: 'closed',
                    children: []
                    };
                for (var i=0; i < data.results.length; i++ ) {
                    all_hosts_node.children.push({
                        data: {
                            title: data.results[i].name, 
                            icon: '/'
                            },
                        attr: {
                            id: data.results[i].id,
                            type: 'host',
                            name: data.results[i].name, 
                            description: data.results[i].description,
                            url: data.results[i].url, 
                            variable_data: data.results[i].varaible_data,
                            inventory: data.results[i].related.inventory,
                            job_events: data.results[i].related.job_events
                            },
                        });
                }
                treeData[0].children.push(all_hosts_node);
                scope.$emit('hostsLoaded');
            })
            .error ( function(data, status, headers, config) {
                Alert('Error', 'Failed to laod tree data. Url: ' + hosts + ' GET status: ' + status);
            });

   
        }
        }]);


