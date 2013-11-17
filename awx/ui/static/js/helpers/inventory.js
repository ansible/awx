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

    .factory('SaveInventory', ['InventoryForm', 'Rest', 'Alert', 'ProcessErrors', 'LookUpInit', 'OrganizationList', 
        'GetBasePath', 'ParseTypeChange', 'LoadInventory', 'Wait',
    function(InventoryForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath, ParseTypeChange,
        LoadInventory, Wait) {
    return function(params) {
        
        // Save inventory property modifications

        var scope = params.scope;
        var form = InventoryForm;
        var defaultUrl=GetBasePath('inventory');

        Wait('start');
     
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
                               Wait('stop');
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
                    Wait('stop');
                    ProcessErrors(scope, data, status, form,
                        { hdr: 'Error!', msg: 'Failed to update inventory. POST returned status: ' + status });
                    });
        }
        catch(err) {
            Wait('stop');
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
        'GetBasePath', 'ParseTypeChange', 'LoadInventory', 'SaveInventory', 'PostLoadInventory',
    function(InventoryForm, GenerateForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath, ParseTypeChange,
        LoadInventory, SaveInventory, PostLoadInventory) {
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
            });

        scope.formModalAction = function() {
            SaveInventory({ scope: scope });
        }    
        
        }
        }]);

