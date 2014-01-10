/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
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

    .factory('SaveInventory', ['InventoryForm', 'Rest', 'Alert', 'ProcessErrors', 'LookUpInit', 'OrganizationList', 
        'GetBasePath', 'ParseTypeChange', 'Wait',
    function(InventoryForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath, ParseTypeChange, Wait) {
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
                               scope.$emit('InventorySaved');
                               })
                           .error( function(data, status, headers, config) {
                               ProcessErrors(scope, data, status, form,
                                  { hdr: 'Error!', msg: 'Failed to update inventory varaibles. PUT returned status: ' + status });
                           });
                    }
                    else {
                        scope.$emit('InventorySaved');
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


    .factory('EditInventoryProperties', ['InventoryForm', 'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LookUpInit', 'OrganizationList', 
        'GetBasePath', 'ParseTypeChange', 'SaveInventory', 'Wait',
    function(InventoryForm, GenerateForm, Rest, Alert, ProcessErrors, LookUpInit, OrganizationList, GetBasePath, ParseTypeChange, SaveInventory,
        Wait) {
    return function(params) {

        var parent_scope = params.scope
        var inventory_id = params.inventory_id; 

        var generator = GenerateForm;
        var form = InventoryForm;
        var defaultUrl=GetBasePath('inventory');
        var master = {}; 

        form.well = false;
        //form.formLabelSize = 'col-lg-3';
        //form.formFieldSize = 'col-lg-9';
        
        var scope = generator.inject(form, {mode: 'edit', modal: true, related: false, modal_show: false });
        
        /* Reset form properties. Otherwise it screws up future requests of the Inventories detail page */
        form.well = true;
        //delete form.formLabelSize;
        //delete form.formFieldSize;

        ParseTypeChange(scope,'inventory_variables', 'inventoryParseType');
        scope.inventoryParseType = 'yaml';
        scope.formModalActionLabel = 'Save';
        scope.formModalCancelShow = true;
        scope.formModalInfo = false;
        scope.formModalHeader = 'Inventory Properties'; 
        
        $('#form-modal .btn-success').removeClass('btn-none').addClass('btn-success');
        
        Wait('start');
        Rest.setUrl(GetBasePath('inventory') + inventory_id + '/');
        Rest.get()
            .success( function(data, status, headers, config) {
                for (var fld in form.fields) {
                    if (fld == 'inventory_variables') {
                        // Parse variables, converting to YAML.  
                        if ($.isEmptyObject(data.variables) || data.variables == "\{\}" || 
                            data.variables == "null" || data.data_variables == "") {
                            scope.inventory_variables = "---";
                        }
                        else {
                            var json_obj = JSON.parse(data.variables);
                            scope.inventory_variables = jsyaml.safeDump(json_obj);
                        }
                        master.inventory_variables = scope.variables;
                    }
                    else if (fld == 'inventory_name') {
                        scope[fld] = data.name;
                        master[fld] = scope[fld];
                    }
                    else if (fld == 'inventory_description') {
                        scope[fld] = data.description;
                        master[fld] = scope[fld];
                    }
                    else if (data[fld]) {
                        scope[fld] = data[fld];
                        master[fld] = scope[fld];
                    }

                    if (form.fields[fld].sourceModel && data.summary_fields &&
                        data.summary_fields[form.fields[fld].sourceModel]) {
                        scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] = 
                            data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                        master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] = 
                            data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                    }
                }

                LookUpInit({
                   scope: scope,
                   form: form,
                   current_item: scope.organization,
                   list: OrganizationList, 
                   field: 'organization' 
                   });
                
                Wait('stop');
                $('#form-modal').modal('show');

                })
            .error( function(data, status, headers, config) {
                Wait('stop');
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get inventory: ' + inventory_id + '. GET returned: ' + status });
                });
       
        if (scope.removeInventorySaved) {
           scope.removeInventorySaved();
        }
        scope.removeInventorySaved = scope.$on('InventorySaved', function() {
            $('#form-modal').modal('hide');           
            });

        scope.formModalAction = function() {
            scope.inventory_id = inventory_id;
            parent_scope.inventory_name = scope.inventory_name;
            console.log('set inventory_name to: ' + parent_scope.inventory_name);
            SaveInventory({ scope: scope });
            } 
        
        }
        }]);

