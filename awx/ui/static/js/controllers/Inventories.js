/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Inventories.js
 *  
 *  Controller functions for the Inventory model.
 *
 */

'use strict';

function InventoriesList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, InventoryList,
                          GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                          ClearScope, ProcessErrors, GetBasePath, Wait)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
    var list = InventoryList;
    var defaultUrl = GetBasePath('inventory');
    var view = GenerateList;
    var paths = $location.path().replace(/^\//,'').split('/');
    var mode = (paths[0] == 'inventories') ? 'edit' : 'select';      // if base path 'users', we're here to add/edit users
    var scope = view.inject(InventoryList, { mode: mode });          // Inject our view
    
    $rootScope.flashMessage = null;
  
    SearchInit({ scope: scope, set: 'inventories', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();
    
    scope.addInventory = function() {
       $location.path($location.path() + '/add');
       }

    scope.editInventory = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteInventory = function(id, name) {
       
       var action = function() {
           var url = defaultUrl + id + '/';
           $('#prompt-modal').modal('hide');
           Wait('start');
           Rest.setUrl(url);
           Rest.destroy()
               .success( function(data, status, headers, config) {
                   scope.search(list.iterator);
                   Wait('stop');
                   })
               .error( function(data, status, headers, config) {
                   Wait('stop');
                   ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                   });      
           };

       Prompt({ hdr: 'Delete', 
                body: 'Are you sure you want to delete ' + name + '?',
                action: action
                });
       }
    
    scope.lookupOrganization = function(organization_id) {
       Rest.setUrl(GetBasePath('organizations') + organization_id + '/');
       Rest.get()
           .success( function(data, status, headers, config) {
               return data.name;
               });
       }


    // Failed jobs link. Go to the jobs tabs, find all jobs for the inventory and sort by status
    scope.viewJobs = function(id) {
       $location.url('/jobs/?inventory__int=' + id + '&order_by=status');
       }

    scope.viewFailedJobs = function(id) {
       $location.url('/jobs/?inventory__int=' + id + '&status=failed&order_by=status');
       }

    scope.editHosts = function(id) {
       $location.url('/inventories/' + id + '/hosts');
       }

    scope.editGroups = function(id) {
       $location.url('/inventories/' + id + '/groups');
       }
}

InventoriesList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'InventoryList', 'GenerateList', 
                            'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
                            'GetBasePath', 'Wait' ];


function InventoriesAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, InventoryForm, 
                         GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
                         GenerateList, OrganizationList, SearchInit, PaginateInit, LookUpInit, GetBasePath,
                         ParseTypeChange) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var defaultUrl = GetBasePath('inventory');
   var form = InventoryForm;
   var generator = GenerateForm;

   form.well = true,
   form.formLabelSize = null;
   form.formFieldSize = null;

   var scope = generator.inject(form, {mode: 'add', related: false});
   scope.inventoryParseType = 'yaml';
   
   generator.reset();
   LoadBreadCrumbs();
   ParseTypeChange(scope,'inventory_variables', 'inventoryParseType');

   LookUpInit({
       scope: scope,
       form: form,
       current_item: ($routeParams.organization_id) ? $routeParams.organization_id : null,
       list: OrganizationList, 
       field: 'organization' 
       });
   
   // Save
   scope.formSave = function() {

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

           Rest.setUrl(defaultUrl);
           Rest.post(data)
               .success( function(data, status, headers, config) {
                   var inventory_id = data.id;
                   if (scope.inventory_variables) {
                      Rest.setUrl(data.related.variable_data);
                      Rest.put(json_data)
                          .success( function(data, status, headers, config) {
                              $location.path('/inventories/' + inventory_id);           
                              })
                          .error( function(data, status, headers, config) {
                              ProcessErrors(scope, data, status, form,
                                 { hdr: 'Error!', msg: 'Failed to add inventory varaibles. PUT returned status: ' + status });
                          });
                   }
                   else {
                      $location.path('/inventories/' + inventory_id);
                   }
                   })
               .error( function(data, status, headers, config) {
                   ProcessErrors(scope, data, status, form,
                       { hdr: 'Error!', msg: 'Failed to add new inventory. Post returned status: ' + status });
                   });
       }
       catch(err) {
           Alert("Error", "Error parsing inventory variables. Parser returned: " + err);  
           }      
       
       };

   // Reset
   scope.formReset = function() {
       // Defaults
       generator.reset();
       }; 
}

InventoriesAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryForm', 'GenerateForm', 
                           'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'GenerateList',
                           'OrganizationList', 'SearchInit', 'PaginateInit', 'LookUpInit', 'GetBasePath', 'ParseTypeChange']; 


function InventoriesEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, InventoryForm, 
                          GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, 
                          RelatedPaginateInit, ReturnToCaller, ClearScope, LookUpInit, Prompt, OrganizationList,
                          GetBasePath, LoadInventory, ParseTypeChange, EditInventory, SaveInventory, PostLoadInventory) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var generator = GenerateForm;
   var form = InventoryForm;
   var defaultUrl=GetBasePath('inventory');
   var scope = generator.inject(form, { mode: 'edit', related: true });
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var id = $routeParams.id;

   scope['inventoryParseType'] = 'yaml';
   scope['inventory_id'] = id;
   
   ParseTypeChange(scope,'inventory_variables', 'inventoryParseType');
   
   // Retrieve each related sets and any lookups
   if (scope.inventoryLoadedRemove) {
      scope.inventoryLoadedRemove();
   }
   scope.inventoryLoadedRemove = scope.$on('inventoryLoaded', function() {
       LoadBreadCrumbs({ path: '/inventories/' + id, title: scope.inventory_name });
       PostLoadInventory({ scope: scope });
       });

   LoadInventory({ scope: scope, doPostSteps: false });

   // Cancel
   scope.formReset = function() {
      generator.reset();
      for (var fld in scope.master) {
          scope[fld] = scope.master[fld];
      }
      };

   // Related set: Add button
   scope.add = function(set) {
      $rootScope.flashMessage = null;
      $location.path('/' + base + '/' + $routeParams.id + '/groups/' + scope.group_id + '/' + set + '/add');
      };

   // Related set: Edit button
   scope.edit = function(set, id, name) {
      $rootScope.flashMessage = null;
      $location.path('/' + base + '/' + $routeParams.id + '/' + set + '/' + id);
      };
   
   if (scope.removeInventorySaved) {
      scope.removeInventorySaved();
   }
   scope.removeInventorySaved = scope.$on('inventorySaved', function() {
       $location.path('/inventories');
       });
   scope.formSave = function() {
      SaveInventory({ scope: scope });
      }

   // Related set: Delete button
   scope['delete'] = function(set, itm_id, name, title) {
      $rootScope.flashMessage = null;
      
      var action = function() {
          var url = defaultUrl + id + '/' + set + '/';
          Rest.setUrl(url);
          Rest.post({ id: itm_id, disassociate: 1 })
              .success( function(data, status, headers, config) {
                  $('#prompt-modal').modal('hide');
                  scope.search(form.related[set].iterator);
                  })
              .error( function(data, status, headers, config) {
                  $('#prompt-modal').modal('hide');
                  ProcessErrors(scope, data, status, null,
                      { hdr: 'Error!', msg: 'Call to ' + url + ' failed. POST returned status: ' + status });
                  });      
          };

       Prompt({ hdr: 'Delete', 
                body: 'Are you sure you want to remove ' + name + ' from ' + scope.name + ' ' + title + '?',
                action: action
                });
       
      };
}

InventoriesEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryForm', 
                            'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                            'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'LookUpInit', 'Prompt',
                            'OrganizationList', 'GetBasePath', 'LoadInventory', 'ParseTypeChange', 'EditInventory', 
                            'SaveInventory', 'PostLoadInventory'
                            ]; 
  
