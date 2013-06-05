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
                          ClearScope, ProcessErrors, GetBasePath)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
    var list = InventoryList;
    var defaultUrl = GetBasePath('inventory');
    var view = GenerateList;
    var paths = $location.path().replace(/^\//,'').split('/');
    var mode = (paths[0] == 'inventories') ? 'edit' : 'select';      // if base path 'users', we're here to add/edit users
    var scope = view.inject(InventoryList, { mode: mode });          // Inject our view
    scope.selected = [];
  
    if (scope.PostRefreshRemove) {
       scope.PostRefreshRemove();
    }
    scope.PostRefreshRemove = scope.$on('PostRefresh', function() {
        $("tr.success").each(function(index) {
            // Make sure no rows have a green background 
            var ngc = $(this).attr('ng-class'); 
            scope[ngc] = ""; 
            });
        });
    
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
           Rest.setUrl(url);
           Rest.delete()
               .success( function(data, status, headers, config) {
                   $('#prompt-modal').modal('hide');
                   scope.search(list.iterator);
                   })
               .error( function(data, status, headers, config) {
                   $('#prompt-modal').modal('hide');
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

    scope.finishSelection = function() {
       Rest.setUrl('/api/v1' + $location.path() + '/');  // We're assuming the path matches the api path. 
                                                         // Will this always be true??
       scope.queue = [];

       scope.$on('callFinished', function() {
          // We call the API for each selected user. We need to hang out until all the api
          // calls are finished.
          if (scope.queue.length == scope.selected.length) {
             // All the api calls finished
             $('input[type="checkbox"]').prop("checked",false);
             scope.selected = [];
             var errors = 0;   
             for (var i=0; i < scope.queue.length; i++) {
                 if (scope.queue[i].result == 'error') {
                    errors++;
                 }
             }
             if (errors > 0) {
                Alert('Error', 'There was an error while adding one or more of the selected inventories.');  
             }
             else {
                ReturnToCaller(1);
             }
          }
          });

       if (scope.selected.length > 0 ) {
          var inventory = null;
          for (var i=0; i < scope.selected.length; i++) {
              for (var j=0; j < scope.inventories.length; j++) {
                  if (scope.inventories[j].id == scope.selected[i]) {
                     inventory = scope.inventories[j];
                  }
              }
              if (inventory !== null) {
                 Rest.post(inventory)
                     .success( function(data, status, headers, config) {
                         scope.queue.push({ result: 'success', data: data, status: status });
                         scope.$emit('callFinished');
                         })
                     .error( function(data, status, headers, config) {
                         scope.queue.push({ result: 'error', data: data, status: status, headers: headers });
                         scope.$emit('callFinished');
                         });
              }
          }
       }
       else {
          ReturnToCaller();
       }  
       }

    scope.toggle_inventory = function(id) {
       if (scope[list.iterator + "_" + id + "_class"] == "success") {
          scope[list.iterator + "_" + id + "_class"] = "";
          document.getElementById('check_' + id).checked = false;
          if (scope.selected.indexOf(id) > -1) {
             scope.selected.splice(scope.selected.indexOf(id),1);
          }
       }
       else {
          scope[list.iterator + "_" + id + "_class"] = "success";
          document.getElementById('check_' + id).checked = true;
          if (scope.selected.indexOf(id) == -1) {
             scope.selected.push(id);
          }
       }
       }
}

InventoriesList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'InventoryList', 'GenerateList', 
                            'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
                            'GetBasePath' ];


function InventoriesAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, InventoryForm, 
                         GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
                         GenerateList, OrganizationList, SearchInit, PaginateInit, LookUpInit, GetBasePath) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var defaultUrl = GetBasePath('inventory');
   var form = InventoryForm;
   var generator = GenerateForm;
   var scope = generator.inject(form, {mode: 'add', related: false});
   generator.reset();
   LoadBreadCrumbs();
   
   LookUpInit({
       scope: scope,
       form: form,
       current_item: ($routeParams.organization_id) ? $routeParams.organization_id : null,
       list: OrganizationList, 
       field: 'organization' 
       });
   
   // Save
   scope.formSave = function() {
      Rest.setUrl(defaultUrl);
      var data = {}
      for (var fld in form.fields) {
          if (form.fields[fld].realName) {
             data[form.fields[fld].realName] = scope[fld];
          }
          else {
             data[fld] = scope[fld];  
          }
      }
      Rest.post(data)
          .success( function(data, status, headers, config) {
              $location.path('/inventories/' + data.id);
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to add new inventory. Post returned status: ' + status });
              });
      };

   // Reset
   scope.formReset = function() {
      // Defaults
      generator.reset();
      }; 
}

InventoriesAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryForm', 'GenerateForm', 
                           'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'GenerateList',
                           'OrganizationList', 'SearchInit', 'PaginateInit', 'LookUpInit', 'GetBasePath' ]; 


function InventoriesEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, InventoryForm, 
                          GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, 
                          RelatedPaginateInit, ReturnToCaller, ClearScope, LookUpInit, Prompt,
                          OrganizationList, TreeInit, GetBasePath, GroupsList, GroupsEdit, LoadInventory,
                          GroupsDelete, HostsList, HostsAdd, HostsEdit, HostsDelete) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var generator = GenerateForm;
   var form = InventoryForm;
   var defaultUrl=GetBasePath('inventory');
   var scope = generator.inject(form, {mode: 'edit', related: true});
   generator.reset();
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var id = $routeParams.id;
   
   scope['inventory_id'] = id;

   // Retrieve each related set and any lookups
   if (scope.inventoryLoadedRemove) {
      scope.inventoryLoadedRemove();
   }
   scope.inventoryLoadedRemove = scope.$on('inventoryLoaded', function() {
       scope.groupTitle = 'All Hosts';
       scope.createButtonShow = false;
       scope.search(scope.relatedSets['hosts'].iterator);
       TreeInit(scope.TreeParams);
       LookUpInit({
           scope: scope,
           form: form,
           current_item: (scope.organization) ? scope.organization : null,
           list: OrganizationList, 
           field: 'organization' 
           });
       });
  
   LoadInventory({ scope: scope });

   // Save changes to the parent
   scope.formSave = function() {
      Rest.setUrl(defaultUrl + $routeParams.id + '/');
      var data = {}
      for (var fld in form.fields) {
          if (form.fields[fld].realName) {
             data[form.fields[fld].realName] = scope[fld];
          }
          else {
             data[fld] = scope[fld];  
          }
      }
      Rest.put(data)
          .success( function(data, status, headers, config) {
              var base = $location.path().replace(/^\//,'').split('/')[0];
              (base == 'inventories') ? ReturnToCaller() : ReturnToCaller(1);
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to update inventory: ' + $routeParams.id + '. PUT status: ' + status });
              });
      };

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

   // Related set: Delete button
   scope.delete = function(set, itm_id, name, title) {
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

   scope.treeController = function($node) {
      var nodeType = $($node).attr('type');
      if (nodeType == 'inventory') {
          return {
              addGroup: {
                  label: 'Add Group',
                  action: function(obj) { GroupsList({ "inventory_id": id, group_id: null }); }
                  }
              }
      }
      else {
         return {
             addGroup: { 
                label: 'Add Subgroup',
                action: function(obj) { GroupsList({ "inventory_id": id, group_id: $(obj).attr('group_id') }); }    
                },
             edit: { 
                 label: 'Edit Group',
                 action: function(obj) { GroupsEdit({ "inventory_id": id, group_id: $(obj).attr('group_id') }); },
                 separator_before: true
                 },
             delete: {
                 label: 'Delete Group',
                 action: function(obj) { GroupsDelete({ scope: scope, "inventory_id": id, group_id: $(obj).attr('group_id') }) }
                 }
             }
      }
      }
  
  scope.$on('NodeSelect', function(e, n) {
      
      // Respond to user clicking on a tree node

      var node = $('li[id="' + n.attr.id + '"]');
      var type = node.attr('type');
      var url;
      scope['selectedNode'] = node;
      $('#tree-view').jstree('open_node',node);
      if (type == 'group') {
         url = node.attr('all');
         scope.groupAddHide = false; 
         scope.groupEditHide =false;
         scope.groupDeleteHide = false;
         scope.createButtonShow = true;
         scope.group_id = node.attr('group_id');
         scope.groupName = n.data;
         scope.groupTitle = n.data;
         scope.groupTitle += (node.attr('description')) ? ' -' + node.attr('description') : '';
      }
      else if (type == 'inventory') {
         url = node.attr('hosts');
         scope.groupAddHide = false; 
         scope.groupEditHide =true;
         scope.groupDeleteHide = true;
         scope.createButtonShow = false;
         scope.groupName = 'All Hosts';
         scope.groupTitle = 'All Hosts';
         scope.group_id = null;
      }
      scope.relatedSets['hosts'] = { url: url, iterator: 'host' };
      RelatedSearchInit({ scope: scope, form: form, relatedSets: scope.relatedSets });
      RelatedPaginateInit({ scope: scope, relatedSets: scope.relatedSets });
      scope.search('host');
      if (!scope.$$phase) {
         scope.$digest();
      }
      });

  scope.addGroup = function() {
      GroupsList({ "inventory_id": id, group_id: scope.group_id });
      }

  scope.editGroup = function() {
      GroupsEdit({ "inventory_id": id, group_id: scope.group_id });
      }

  scope.deleteGroup = function() {
      GroupsDelete({ scope: scope, "inventory_id": id, group_id: scope.group_id });
      }
  
  scope.addHost = function() {
      HostsList({ scope: scope, "inventory_id": id, group_id: scope.group_id });
      }

  scope.editHost = function(host_id, host_name) {
      HostsEdit({ scope: scope, "inventory_id": id, group_id: scope.group_id, host_id: host_id, host_name: host_name });
      }

  scope.deleteHost = function(host_id, host_name) {
      HostsDelete({ scope: scope, "inventory_id": id, group_id: scope.group_id, host_id: host_id, host_name: host_name });
      }

}

InventoriesEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryForm', 
                            'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                            'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'LookUpInit', 'Prompt',
                            'OrganizationList', 'TreeInit', 'GetBasePath', 'GroupsList', 'GroupsEdit', 'LoadInventory',
                            'GroupsDelete', 'HostsList', 'HostsAdd', 'HostsEdit', 'HostsDelete'
                            ]; 
  