/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  InventoryHelper
 *  Routines shared amongst the inventory controllers 
 */
 
angular.module('InventoryHelper', [ 'RestServices', 'Utilities', 'OrganizationListDefinition',
                                    'SearchHelper', 'PaginateHelper', 'ListGenerator', 'AuthService'
                                    ]) 

    .factory('TreeInit', ['Alert', 'Rest', 'Authorization',
    function(Alert, Rest, Authorization) {
    return function(params) {

        var scope = params.scope;
        var inventory = params.inventory;
        var groups = inventory.related.groups;
        var hosts = inventory.related.hosts; 
        var inventory_name = inventory.name; 
        var inventory_url = inventory.url;
        var inventory_id = inventory.id;
        
        var treeData = [];

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
                   
                    var tree_id = '#tree-view';
                    //.bind("open_node.jstree close_node.jstree", function (e,data) {
                    //    var currentNode = data.args[0];
                    //    if (e.type === "open_node") {
                            //var tree = $.jstree._reference(tree_id);
                            //tree.refresh(currentNode);
                    //    }
                    //    })
                    $(tree_id).jstree({
                        "core": { "initially_open":['inventory-node'] },
                        "plugins": ['themes', 'json_data', 'ui', 'contextmenu'],
                        "json_data": {
                            data: treeData,
                            ajax: {
                                url: function(node){
                                    return $(node).attr('all');
                                    },
                                headers: { 'Authorization': 'Token ' + Authorization.getToken() },
                                success: function(data) {
                                    console.log(data);
                                    },
                                error: function() {
                                    if (console) {
                                       console.log('Error accessing node data!');
                                    }
                                    }
                                }
                            },
                        "contextmenu": {
                            items: scope.treeController
                            }
                        });
                    })
                .error( function(data, status, headers, config) {
                    Alert('Error', 'Failed to laod tree data. Url: ' + groups + ' GET status: ' + status);
                    });
            });

        Rest.setUrl(hosts + '?order_by=name'); 
        Rest.get()
            .success ( function(data, status, headers, config) {
                treeData = [];
                treeData.push({ 
                    data: {
                        title: inventory_name,
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
                for (var i=0; i < data.results.length; i++ ) {
                    treeData[0].children.push({
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
                scope.$emit('hostsLoaded');
            })
            .error ( function(data, status, headers, config) {
                Alert('Error', 'Failed to laod tree data. Url: ' + hosts + ' GET status: ' + status);
            });

   
        }
        }]);


