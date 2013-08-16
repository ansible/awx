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
                                    'InventoryFormDefinition', 'ParseHelper'
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
        if (scope.inventoryLoadedRemove) {
            scope.inventoryLoadedRemove();
        }
        scope.inventoryLoadedRemove = scope.$on('inventoryLoaded', function() {
            var filter = (scope.inventoryFailureFilter) ? "has_active_failures=true&" : ""; 
            var url = groups + '?' + filter + 'order_by=name';
            var title;
            Rest.setUrl(url);
            Rest.get()
                .success( function(data, status, headers, config) {    
                    for (var i=0; i < data.results.length; i++) {
                        title = data.results[i].name; 
                        title += (data.results[i].has_active_failures) ? ' <span class="tree-badge" title="Contains hosts with failed jobs">' +
                            '<i class="icon-exclamation-sign"></i></span>' : ''; 
                        treeData[0].children.push({
                           data: {
                               title: title
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
                    scope.$emit('buildTree', treeData, idx);
                    })
                .error( function(data, status, headers, config) {
                    Alert('Error', 'Failed to laod tree data. Url: ' + groups + ' GET status: ' + status);
                    });
            });

          var title = inventory_name;
          title += (has_active_failures) ? ' <span class="tree-badge" title="Contains hosts with failed jobs">' +
              '<i class="icon-exclamation-sign"></i></span>' : ''; 
          treeData =
              [{ 
              data: {
                  title: title
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
          scope.$emit('inventoryLoaded');
           
        }
        }])


    .factory('TreeInit', ['Alert', 'Rest', 'Authorization', '$http', 'LoadTreeData', 'GetBasePath', 'ProcessErrors', 'Wait',
    function(Alert, Rest, Authorization, $http, LoadTreeData, GetBasePath, ProcessErrors, Wait) {
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
                "core": { "initially_open":['inventory_node'], 
                    "html_titles": true
                    },
                "plugins": ['themes', 'json_data', 'ui', 'contextmenu', 'dnd', 'crrm'],
                "themes": {
                    "theme": "ansible",
                    "dots": false,
                    "icons": true
                    },
                "ui": { 
                    "initially_select": [ 'inventory-node' ],
                    "select_limit": 1 
                    },
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
                            var title;
                            var filter = (scope.inventoryFailureFilter) ? "has_active_failures=true&" : ""; 
                            for (var i=0; i < data.results.length; i++) {
                                title = data.results[i].name; 
                                title += (data.results[i].has_active_failures) ? ' <span class="tree-badge" title="Contains hosts with failed jobs">' +
                                    '<i class="icon-exclamation-sign"></i></span>' : ''; 
                                response.push({
                                    data: {
                                       title: title
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
                "dnd": { },
                "crrm": { 
                    "move": {
                        "check_move": function(m) {
                            if (m.op.attr('id') == m.np.attr('id')) {
                               // old parent and new parent cannot be the same
                               return false;
                            }
                            return true;
                            }
                        }
                    },
                "crrm" : { },
                "contextmenu": {
                    items: scope.treeController
                    }
                });
  
            $(tree_id).bind("loaded.jstree", function () {
                scope['treeLoading'] = false;
                scope.$emit('treeLoaded');
                });

            $(tree_id).bind('move_node.jstree', function(e, data) {
                // When user drags-n-drops a node, update the API 
                
                Wait('start');

                var node, target, url, parent, inv_id, variables;
                node = $('#tree-view li[id="' + data.rslt.o[0].id + '"]');  // node being moved
                parent = $('#tree-view li[id="' + data.args[0].op[0].id + '"]');  //node moving from
                target = $('#tree-view li[id="' + data.rslt.np[0].id + '"]');  // node moving to
                inv_id = inventory_id;
                
                function cleanUp() {
                    Wait('stop');
                    if (!scope.$$phase) {
                       scope.$digest();
                    } 
                }

                if (scope.removeCopyVariables) {
                   scope.removeCopyVariables();
                }
                scope.removeCopyVariables = scope.$on('copyVariables', function(e, id, url) {
                    if (variables) {
                       Rest.setUrl(url); 
                       Rest.put(variables)
                           .success(function(data, status, headers, config) {
                               cleanUp();
                               })
                           .error(function(data, status, headers, config) {
                               cleanUp();
                               ProcessErrors(scope, data, status, null,
                                   { hdr: 'Error!', msg: 'Failed to update variables. PUT returned status: ' + status });
                               });
                    }
                    else {
                       cleanUp();
                    }
                    }); 
                
                if (scope['addToTargetRemove']) {
                   scope.addToTargetRemove();
                }
                scope.addToTargetRemove = scope.$on('addToTarget', function() {
                   // add the new group to the target parent
                   var url = (target.attr('type') == 'group') ? GetBasePath('base') + 'groups/' + target.attr('group_id') + '/children/' :
                       GetBasePath('inventory') + inv_id + '/groups/';
                   var group = { 
                       name: node.attr('name'),
                       description: node.attr('description'),
                       inventory: node.attr('inventory')
                       }
                   Rest.setUrl(url);
                   Rest.post(group)
                       .success( function(data, status, headers, config) {
                           //Update the node with new attributes
                           var filter = (scope.inventoryFailureFilter) ? "has_active_failures=true&" : ""; 
                           node.attr('group_id', data.id);
                           node.attr('variable', data.related.variable_data);
                           node.attr('all', data.related.all_hosts); 
                           node.attr('children', data.related.children + '?' + filter + 'order_by=name');
                           node.attr('hosts', data.related.hosts);
                           node.attr('data-failures', data.has_active_failures);
                           scope.$emit('copyVariables', data.id, data.related.variable_data);
                           })
                       .error( function(data, status, headers, config) {
                           cleanUp();
                           ProcessErrors(scope, data, status, null,
                              { hdr: 'Error!', msg: 'Failed to add ' + node.attr('name') + ' to ' + 
                              target.attr('name') + '. POST returned status: ' + status });
                           });
                   });

                // disassociate the group from the original parent
                if (scope.removeGroupRemove) {
                   scope.removeGroupRemove(); 
                }
                scope.removeGroupRemove = scope.$on('removeGroup', function() {
                    var url = (parent.attr('type') == 'group') ? GetBasePath('base') + 'groups/' + parent.attr('group_id') + '/children/' : 
                        GetBasePath('inventory') + inv_id + '/groups/';
                    Rest.setUrl(url);
                    Rest.post({ id: node.attr('group_id'), disassociate: 1 })
                        .success( function(data, status, headers, config) {
                            scope.$emit('addToTarget');
                            })
                        .error( function(data, status, headers, config) {
                            cleanUp();
                            ProcessErrors(scope, data, status, null,
                                { hdr: 'Error!', msg: 'Failed to remove ' + node.attr('name') + ' from ' + 
                                  parent.attr('name') + '. POST returned status: ' + status });
                            });
                    });
                
                // Lookup the inventory. We already have what we need except for variables.
                Rest.setUrl(GetBasePath('base') + 'groups/' + node.attr('group_id') + '/');
                Rest.get()
                    .success( function(data, status, headers, config) {
                        variables = (data.variables) ? JSON.parse(data.variables) : "";
                        scope.$emit('removeGroup');
                        })
                    .error( function(data, status, headers, config) {
                        cleanUp();
                        ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Failed to lookup group ' + node.attr('name') + 
                            '. GET returned status: ' + status });
                        });
                
                //scope['treeLoading'] = true;

                if (!scope.$$phase) {
                   scope.$digest();
                } 
                });
            
            // When user clicks on a group, display the related hosts in the list view
            $(tree_id).bind("select_node.jstree", function(e, data){
                scope.$emit('NodeSelect', data.inst.get_json()[0]);
                });
            
            });
        
        scope['treeLoading'] = true;
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

                scope.TreeParams = { scope: scope, inventory: data };
                scope.variable_url = data.related.variable_data;
                scope.relatedSets['hosts'] = { url: data.related.hosts, iterator: 'host' };
                
                // Load the tree view
                if (params.doPostSteps) {
                   RelatedSearchInit({ scope: scope, form: form, relatedSets: scope.relatedSets });
                   RelatedPaginateInit({ scope: scope, relatedSets: scope.relatedSets });
                }
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
        scope = angular.element(getElementById('htmlTemplate')).scope();
        scope['selectedNodeName'] = name;
        scope['selectedNodeName'] += (node.attr('data-failures') == 'true') ? 
           ' <span class="nav-badge"><i class="icon-exclamation-sign" title="Contains hosts with failed jobs"></i></span>' : '';
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
                  node = $('#tree-view li[id="' + selectedId + '"]');
                  $('#tree-view').jstree('select_node', node);
                  //$('#tree-view li[id="' + selectedId + '"] a').first().click();
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

        scope.treeLoading = true;
        LoadInventory({ scope: scope, doPostSteps: true });
        
        }
        }])


    .factory('EditInventory', ['InventoryForm', 'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LookUpInit', 'OrganizationList', 
        'GetBasePath', 'ParseTypeChange', 'LoadInventory', 'RefreshGroupName',
    function(InventoryForm, GenerateForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath, ParseTypeChange,
        LoadInventory, RefreshGroupName) {
    return function(params) {

        var generator = GenerateForm;
        var form = InventoryForm;
        var defaultUrl=GetBasePath('inventory');
        var scope = params.scope

        generator.inject(form, {mode: 'edit', modal: true, related: false});
        
        ParseTypeChange(scope,'inventory_variables', 'inventoryParseType');

        scope.inventoryParseType = 'yaml';
        scope['inventory_id'] = params['inventory_id'];
        scope.formModalActionLabel = 'Save';
        scope.formModalCancelShow = true;
        scope.formModalInfo = false;
        $('#form-modal .btn-success').removeClass('btn-none').addClass('btn-success');
        scope.formModalHeader = 'Inventory Properties'; 
        
        // Retrieve each related set and any lookups
        if (scope.inventoryLoadedRemove) {
           scope.inventoryLoadedRemove();
        }
        scope.inventoryLoadedRemove = scope.$on('inventoryLoaded', function() {
           
           LookUpInit({
               scope: scope,
               form: form,
               current_item: (scope.organization !== undefined) ? scope.organization : null,
               list: OrganizationList, 
               field: 'organization' 
               });

           if (scope.variable_url) {
              Rest.setUrl(scope.variable_url);
              Rest.get()
                  .success( function(data, status, headers, config) {
                      if ($.isEmptyObject(data)) {
                         scope.inventory_variables = "---";
                      }
                      else {
                         scope.inventory_variables = jsyaml.safeDump(data);
                      }
                      })
                  .error( function(data, status, headers, config) {
                      scope.inventory_variables = null;
                      ProcessErrors(scope, data, status, form,
                          { hdr: 'Error!', msg: 'Failed to retrieve inventory variables. GET returned status: ' + status });
                      });
           }
           else {
              scope.inventory_variables = "---";
           }
           if (!scope.$$phase) {
              scope.$digest();
           } 
           });

        LoadInventory({ scope: scope, doPostSteps: false });
        
        if (!scope.$$phase) {
           scope.$digest();
        }

        function PostSave() {
           $('#form-modal').modal('hide');

           // Make sure the inventory name appears correctly in the tree and the navbar
           RefreshGroupName($('#inventory-node'), scope['inventory_name'], scope['inventory_description']);
          
           // Reset the form to disable the form action buttons
           //scope[form.name + '_form'].$setPristine();

           // Show the flash message for 5 seconds, letting the user know the save worked
           //scope['flashMessage'] = 'Your changes were successfully saved!';
           //setTimeout(function() {
           //    scope['flashMessage'] = null;
           //    if (!scope.$$phase) {
           //       scope.$digest();
           //    } 
           //    }, 5000);
           }

        // Save
        scope.formModalAction = function() {
           try { 
               // Make sure we have valid variable data
               if (scope.inventoryParseType == 'json') {
                  var json_data = JSON.parse(scope.inventory_variables);  //make sure JSON parses
               }
               else {
                  var json_data = jsyaml.load(scope.inventory_variables);  //parse yaml
               }

               // Make sure our JSON is actually an object
               if (typeof json_data !== 'object') {
                  throw "failed to return an object!";
               }

               var data = {}
               for (var fld in form.fields) {
                   if (fld != 'inventory_variables') {
                      if (form.fields[fld].realName) {
                         data[form.fields[fld].realName] = scope[fld];
                      }
                      else {
                         data[fld] = scope[fld];  
                      }
                   }
               }

               Rest.setUrl(defaultUrl + scope['inventory_id'] + '/');
               Rest.put(data)
                   .success( function(data, status, headers, config) {
                       if (scope.inventory_variables) {
                          Rest.setUrl(data.related.variable_data);
                          Rest.put(json_data)
                              .success( function(data, status, headers, config) {
                                  PostSave();
                                  })
                              .error( function(data, status, headers, config) {
                                  ProcessErrors(scope, data, status, form,
                                     { hdr: 'Error!', msg: 'Failed to update inventory varaibles. PUT returned status: ' + status });
                              });
                       }
                       else {
                          PostSave();
                       }
                       })
                   .error( function(data, status, headers, config) {
                       ProcessErrors(scope, data, status, form,
                           { hdr: 'Error!', msg: 'Failed to update inventory. POST returned status: ' + status });
                       });
           }
           catch(err) {
               Alert("Error", "Error parsing inventory variables. Parser returned: " + err);  
               }      
           
           };
    }
    }]);

