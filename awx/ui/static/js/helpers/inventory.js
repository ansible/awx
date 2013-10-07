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
                                    'InventoryFormDefinition', 'ParseHelper', 'InventorySummaryDefinition'
                                    ]) 

    .factory('LoadTreeData', ['Alert', 'Rest', 'Authorization', '$http', 'Wait', 'SortNodes',
    function(Alert, Rest, Authorization, $http, Wait, SortNodes) {
    return function(params) {

        var scope = params.scope;
        var inventory = params.inventory;
        var group_id = params.group_id; 
        var group_idx;
        var groups = inventory.related.root_groups;
        var hosts = inventory.related.hosts; 
        var inventory_name = inventory.name; 
        var inventory_url = inventory.url;
        var inventory_id = inventory.id;
        var has_active_failures = inventory.has_active_failures;
        var inventory_descr = inventory.description;
        var idx=0;
        var treeData =
            [{ 
                data: {
                    title: inventory_name + ' Inventory Groups'
                    }, 
                attr: {
                    type: 'inventory',
                    id: 'inventory-node',
                    url: inventory_url,
                    'inventory_id': inventory_id,
                    name: inventory_name,
                    description: inventory_descr,
                    "data-failures": inventory.has_active_failures
                    },
                state: 'open',
                children:[] 
                }];

        function addNodes(tree, data) {
            var sorted = SortNodes(data);
            for (var i=0; i < sorted.length; i++) {
                tree.children.push({
                    data: {
                        title: sorted[i].name
                        },
                    attr: {
                        id: idx,
                        group_id: sorted[i].id,
                        type: 'group',
                        name: sorted[i].name, 
                        description: sorted[i].description,
                        "data-failures": sorted[i].has_active_failures,
                        inventory: sorted[i].inventory
                        },
                    state: 'open',
                    children:[]
                    });
                if (sorted[i].id == group_id) {
                   group_idx = idx;  
                }
                idx++;
                if (sorted[i].children.length > 0) {
                   var node = tree.children.length - 1;
                   addNodes(tree.children[node], sorted[i].children);
                }
            }
            }

        Rest.setUrl(scope.treeData); 
        Rest.get()
            .success( function(data, status, headers, config) {
                var sorted = SortNodes(data);
                addNodes(treeData[0], sorted);
                scope.$emit('buildTree', treeData, idx, group_idx);  
            })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve inventory tree data. GET returned status: ' + status });
            });

        }
        }])


    .factory('TreeInit', ['Alert', 'Rest', 'Authorization', '$http', 'LoadTreeData', 'GetBasePath', 'ProcessErrors', 'Wait',
        'LoadRootGroups',
    function(Alert, Rest, Authorization, $http, LoadTreeData, GetBasePath, ProcessErrors, Wait, LoadRootGroups) {
    return function(params) {

        var scope = params.scope;
        var inventory = params.inventory;
        var group_id = params.group_id;

        var groups = inventory.related.root_groups;
        var hosts = inventory.related.hosts; 
        var inventory_name = inventory.name; 
        var inventory_url = inventory.url;
        var inventory_id = inventory.id;
        var inventory_descr = inventory.description;
        var tree_id = '#tree-view';
        var json_tree_data; 

        // After loading the Inventory top-level data, initialize the tree
        if (scope.buildTreeRemove) {
           scope.buildTreeRemove();
        }
        scope.buildTreeRemove = scope.$on('buildTree', function(e, treeData, index, group_idx) {
            var idx = index;
            var selected = (group_idx !== undefined && group_idx !== null) ? group_idx : 'inventory-node';
            json_tree_data = treeData;

            $(tree_id).jstree({
                "core": { //"initially_open":['inventory-node'],
                    "html_titles": true
                    },
                "plugins": ['themes', 'json_data', 'ui', 'dnd', 'crrm', 'sort'],
                "themes": {
                    "theme": "ansible",
                    "dots": false,
                    "icons": true
                    },
                "ui": { 
                    "initially_select": [ selected ],
                    "select_limit": 1
                    },
                "json_data": {
                    data: json_tree_data
                    },
                "dnd": { },
                "crrm": { 
                    "move": {
                        "check_move": function(m) {
                            if (m.np.attr('id') == 'tree-view') {
                               return false;
                            }
                            if (m.op.attr('id') == m.np.attr('id')) {
                               // old parent and new parent cannot be the same
                               return false;
                            }
                            return true;
                            }
                        }
                    },
                "crrm" : { }
                });
            });
            
        $(tree_id).bind("loaded.jstree", function () {
            scope['treeLoading'] = false;
            Wait('stop');
            // Force root node styling changes
            $('#inventory-node ins').first().remove();
            $('#inventory-node a ins').first().css('background-image', 'none').append('<i class="icon-sitemap"></i>').css('margin-right','10px');
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
                LoadRootGroups({ scope: scope });
                Wait('stop');
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

            if (!scope.$$phase) {
               scope.$digest();
            } 
            });
            
        // When user clicks on a group
        $(tree_id).bind("select_node.jstree", function(e, data){
            scope.$emit('NodeSelect', data.inst.get_json()[0]);
            });
            
        Wait('start');
        LoadTreeData(params);
        
        }
        }])

    .factory('LoadRootGroups', ['Rest', 'ProcessErrors', function(Rest, ProcessErrors) {
    return function(params) {
        
        // Build an array of root group IDs. We'll need this when copying IDs.
        
        var scope = params.scope;
        Rest.setUrl(scope.inventoryRootGroupsUrl);
        Rest.get()
            .success( function(data, status, headers, config) {
                scope.inventoryRootGroups = [];
                for (var i=0; i < data.results.length; i++){
                    scope.inventoryRootGroups.push(data.results[i].id);
                } 
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to retrieve root groups for inventory: ' + 
                    scope.inventory_id + '. GET status: ' + status });
                });
        }  
        }])

    .factory('LoadInventory', ['$routeParams', 'Alert', 'Rest', 'Authorization', '$http', 'ProcessErrors',
        'RelatedSearchInit', 'RelatedPaginateInit', 'GetBasePath', 'LoadBreadCrumbs', 'InventoryForm', 'LoadRootGroups',
    function($routeParams, Alert, Rest, Authorization, $http, ProcessErrors, RelatedSearchInit, RelatedPaginateInit,
        GetBasePath, LoadBreadCrumbs, InventoryForm, LoadRootGroups) {
    return function(params) {
        
        // Load inventory detail record
        
        var scope = params.scope;
        var form = InventoryForm;
        scope.relatedSets = [];
        scope.master = {};
        
        if (scope.removeLevelOneGroups) {
           scope.removeLevelOneGroups();
        }
        scope.removeLevelOneGroups = scope.$on('inventoryLoaded', function() {
            LoadRootGroups({ scope: scope });
            });

        Rest.setUrl(GetBasePath('inventory') + scope['inventory_id'] + '/');
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
                
                scope.inventoryGroupsUrl = data.related.groups;
                scope.inventoryRootGroupsUrl = data.related.root_groups;
                scope.TreeParams = { scope: scope, inventory: data };
                scope.variable_url = data.related.variable_data;
                scope.relatedSets['hosts'] = { url: data.related.hosts, iterator: 'host' };
                scope.treeData = data.related.tree;

                // Load the tree view
                if (params.doPostSteps) {
                   RelatedSearchInit({ scope: scope, form: form, relatedSets: scope.relatedSets });
                   RelatedPaginateInit({ scope: scope, relatedSets: scope.relatedSets });
                }
                scope.$emit('inventoryLoaded');
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to retrieve inventory: ' + $routeParams.id + '. GET status: ' + status });
                });

        }
        }])


    .factory('RefreshGroupName', [ function() {
    return function(node, name, description) {
        // Call after GroupsEdit controller saves changes
        $('#tree-view').jstree('rename_node', node, name);
        node.attr('description', description);
        scope = angular.element(document.getElementById('htmlTemplate')).scope();
        scope['selectedNodeName'] = name;
        }
        }])


    .factory('RefreshTree', ['Alert', 'Rest', 'Authorization', '$http', 'TreeInit', 'LoadInventory',
    function(Alert, Rest, Authorization, $http, TreeInit, LoadInventory) {
    return function(params) {

        // Call after an Edit or Add to refresh tree data
        
        var scope = params.scope;
        var group_id = params.group_id;
        
        /*
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
        */
        
        if (scope.inventoryLoadedRemove) {
           scope.inventoryLoadedRemove();
        }
        scope.inventoryLoadedRemove = scope.$on('inventoryLoaded', function() {
            // Get the list of open tree nodes starting with the current group and going up 
            // the tree until we hit the inventory or root node.
            /*
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
            */
            $('#tree-view').jstree('destroy');
            scope.TreeParams.group_id = group_id;
            TreeInit(scope.TreeParams);  
            });

        scope.treeLoading = true;
        LoadInventory({ scope: scope, doPostSteps: true });
        
        }
        }])

   
    .factory('SaveInventory', ['InventoryForm', 'Rest', 'Alert', 'ProcessErrors', 'LookUpInit', 'OrganizationList', 
        'GetBasePath', 'ParseTypeChange', 'LoadInventory', 'RefreshGroupName',
    function(InventoryForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath, ParseTypeChange,
        LoadInventory, RefreshGroupName) {
    return function(params) {
        
        // Save inventory property modifications

        var scope = params.scope;
        var form = InventoryForm;
        var defaultUrl=GetBasePath('inventory');
     
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
                               scope.$emit('inventorySaved');
                               })
                           .error( function(data, status, headers, config) {
                               ProcessErrors(scope, data, status, form,
                                  { hdr: 'Error!', msg: 'Failed to update inventory varaibles. PUT returned status: ' + status });
                           });
                    }
                    else {
                        scope.$emit('inventorySaved');
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
    }
    }])

    .factory('PostLoadInventory', ['InventoryForm', 'Rest', 'Alert', 'ProcessErrors', 'LookUpInit', 'OrganizationList', 'GetBasePath',
    function(InventoryForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath) {
    return function(params) {
        
        var scope = params.scope;
        
        LookUpInit({
            scope: scope,
            form: InventoryForm,
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
                   scope.master.inventory_variables = scope.inventory_variables;
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
    }
    }])

    .factory('EditInventory', ['InventoryForm', 'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LookUpInit', 'OrganizationList', 
        'GetBasePath', 'ParseTypeChange', 'LoadInventory', 'RefreshGroupName', 'SaveInventory', 'PostLoadInventory',
    function(InventoryForm, GenerateForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath, ParseTypeChange,
        LoadInventory, RefreshGroupName, SaveInventory, PostLoadInventory) {
    return function(params) {

        var generator = GenerateForm;
        var form = InventoryForm;
        var defaultUrl=GetBasePath('inventory');
        var scope = params.scope
        
        form.well = false;
        form.formLabelSize = 'col-lg-3';
        form.formFieldSize = 'col-lg-9';
        
        generator.inject(form, {mode: 'edit', modal: true, related: false});
        
        /* Reset form properties. Otherwise it screws up future requests of the Inventories detail page */
        form.well = true;
        delete form.formLabelSize;
        delete form.formFieldSize;

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
           PostLoadInventory({ scope: scope });
           });

        LoadInventory({ scope: scope, doPostSteps: false });
        
        if (!scope.$$phase) {
           scope.$digest();
        }

        if (scope.removeInventorySaved) {
           scope.removeInventorySaved();
        }
        scope.removeInventorySaved = scope.$on('inventorySaved', function() {
            $('#form-modal').modal('hide');           
            // Make sure the inventory name appears correctly in the tree and the navbar
            RefreshGroupName($('#inventory-node'), scope['inventory_name'], scope['inventory_description']);
           });

        scope.formModalAction = function() {
            SaveInventory({ scope: scope });
        }
        
    }
    }])

    .factory('SetShowGroupHelp', ['Rest', 'ProcessErrors', 'GetBasePath', function(Rest, ProcessErrors, GetBasePath) {
    return function(params) {
        // Check if inventory has groups. If not, turn on hints to let user know groups are required
        // before hosts can be added
        var scope = params.scope;
        var url = GetBasePath('inventory') + scope.inventory_id + '/groups/';
        Rest.setUrl(url);
        Rest.get()
            .success( function(data, status, headers, config) {
                if (data.results.length > 0) {
                   scope.showGroupHelp = false;
                }
                else {
                   scope.showGroupHelp = true;
                }
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, form,
                    { hdr: 'Error!', msg: 'Failed to retrieve inventory groups. GET returned status: ' + status });
                });
    }
    }])

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
    }]);

