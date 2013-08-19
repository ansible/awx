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
           Rest.setUrl(url);
           Rest.destroy()
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


    // Failed jobs link. Go to the jobs tabs, find all jobs for the inventory and sort by status
    scope.viewJobs = function(id) {
       $location.url('/jobs/?inventory__int=' + id + '&order_by=status');
       }
}

InventoriesList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'InventoryList', 'GenerateList', 
                            'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
                            'GetBasePath' ];


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
                          RelatedPaginateInit, ReturnToCaller, ClearScope, LookUpInit, Prompt,
                          OrganizationList, TreeInit, GetBasePath, GroupsList, GroupsAdd, GroupsEdit, LoadInventory,
                          GroupsDelete, HostsList, HostsAdd, HostsEdit, HostsDelete, RefreshGroupName, ParseTypeChange,
                          HostsReload, EditInventory, RefreshTree, LoadSearchTree) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var generator = GenerateForm;
   var form = InventoryForm;
   var defaultUrl=GetBasePath('inventory');
   var scope = generator.inject(form, {mode: 'edit', related: true, buildTree: true});
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var id = $routeParams.id;
   
   ParseTypeChange(scope,'inventory_variables', 'inventoryParseType');
   
   $('#inventory-tabs a:first').tab('show');  //activate the hosts tab

   scope['inventoryParseType'] = 'yaml';
   scope['inventory_id'] = id;
   scope['inventoryFailureFilter'] = false;

   // Retrieve each related sets and any lookups
   if (scope.inventoryLoadedRemove) {
      scope.inventoryLoadedRemove();
   }
   scope.inventoryLoadedRemove = scope.$on('inventoryLoaded', function() {
       LoadSearchTree({ scope: scope, inventory_id: scope['inventory_id'] });
       TreeInit(scope.TreeParams);
       if (!scope.$$phase) {
          scope.$digest();
       }
       });

   // Add the selected flag to the hosts set.
   if (scope.relatedHostsRemove) {
      scope.relatedHostsRemove(); 
   }
   scope.relatedHostsRemove = scope.$on('relatedhosts', function() {
       scope.toggleAllFlag = false;
       for (var i=0; i < scope.hosts.length; i++) {
           scope.hosts[i].selected = 0;
       }
       });

   LoadInventory({ scope: scope, doPostSteps: true });
   $('#inventory-tabs a[href="#inventory-hosts"]').on('show.bs.tab', function() { 
       scope['hosts'] = null;
       LoadSearchTree({ scope: scope, inventory_id: scope['inventory_id'] });
       if (!scope.$$phase) {
          scope.$digest();
       }
       });

   scope.filterInventory = function() {
      $rootScope.hostFailureFilter = scope.hostFailureFilter;
      LoadSearchTree({ scope: scope, inventory_id: scope['inventory_id'] });
      //HostsReload({ scope: scope, inventory_id: scope['inventory_id'], group_id: scope['group_id'] });
   }

   scope.filterHosts = function() {
      HostsReload({ scope: scope, inventory_id: scope['inventory_id'], group_id: scope['group_id'] });
   }

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

   scope.editInventory = function() {
      EditInventory({ scope: scope, 'inventory_id': scope['inventory_id'] });
      };

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

   scope.treeController = function($node) {

      var nodeType = $($node).attr('type');
      if (nodeType == 'inventory') {
          return {
              editInventory: {
                  label: 'Inventory Properties',
                  action: function(obj) {
                      scope.group_id = null;
                      if (!scope.$$phase) {
                         scope.$digest();
                      }
                      EditInventory({ scope: scope, "inventory_id": id });
                      },
                  separator_after: true
                  },
              addGroup: {
                  label: 'Create New Group',
                  action: function(obj) {
                      scope.group_id = null;
                      if (!scope.$$phase) {
                         scope.$digest();
                      }
                      GroupsAdd({ "inventory_id": id, group_id: null });
                      }
                  }
              }
      }
      else {
         return {
             edit: { 
                 label: 'Group Properties',
                 action: function(obj) {
                     scope.group_id = $(obj).attr('group_id');
                     if (!scope.$$phase) {
                        scope.$digest();
                     }
                     GroupsEdit({ "inventory_id": id, group_id: $(obj).attr('group_id') }); 
                     },
                 separator_after: true
                 },

             addGroup: { 
                 label: 'Add Existing Group',
                 action: function(obj) {
                     scope.group_id = $(obj).attr('group_id');
                     if (!scope.$$phase) {
                        scope.$digest();
                     }
                     GroupsList({ "inventory_id": id, group_id: $(obj).attr('group_id') });
                     }    
                 },

             createGroup: { 
                 label: 'Create New Group',
                 action: function(obj) {
                     scope.group_id = $(obj).attr('group_id');
                     if (!scope.$$phase) {
                        scope.$digest();
                     }
                     GroupsAdd({ "inventory_id": id, group_id: $(obj).attr('group_id') });
                     }    
                 },

             "delete": {
                 label: 'Delete Group',
                 action: function(obj) {
                     scope.group_id = $(obj).attr('group_id');
                     if (!scope.$$phase) {
                        scope.$digest();
                     }
                     GroupsDelete({ scope: scope, "inventory_id": id, group_id: $(obj).attr('group_id') });
                     }
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
      scope['selectedNodeName'] = node.attr('name');
      
      $('#tree-view').jstree('open_node',node);
      
      if (type == 'group') {
         url = node.attr('all');
         scope.groupAddHide = false;
         scope.groupCreateHide = false;
         scope.groupEditHide = false;
         scope.inventoryEditHide = true;
         scope.groupDeleteHide = false;
         scope.createButtonShow = true;
         //scope.group_id = node.attr('group_id');
         //scope.groupName = n.data;
         //scope.groupTitle = '<h4>' + n.data + '</h4>';
         //scope.groupTitle += (node.attr('description')) ? '<p>' + node.attr('description') + '</p>' : '';
      }
      else if (type == 'inventory') {
         url = node.attr('hosts');
         scope.groupAddHide = true;
         scope.groupCreateHide = false; 
         scope.groupEditHide =true;
         scope.inventoryEditHide=false;
         scope.groupDeleteHide = true;
         scope.createButtonShow = false;
         //scope.groupName = 'All Hosts';
         //scope.groupTitle = '<h4>All Hosts</h4>';
         //scope.group_id = null;
      }

      if (!scope.$$phase) {
         scope.$digest();
      }
      });

  scope.addGroup = function() {
      GroupsList({ "inventory_id": id, group_id: scope.group_id });
      }

  scope.createGroup = function() {
      GroupsAdd({ "inventory_id": id, group_id: scope.group_id });
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

  scope.createHost = function() {
      HostsAdd({ scope: scope, "inventory_id": id, group_id: scope.group_id });
      }

  scope.editHost = function(host_id, host_name) {
      HostsEdit({ scope: scope, "inventory_id": id, group_id: scope.group_id, host_id: host_id, host_name: host_name });
      }

  scope.deleteHost = function(host_id, host_name) {
      HostsDelete({ scope: scope, "inventory_id": id, group_id: scope.group_id, host_id: host_id, host_name: host_name,
          request: 'delete' });
      }

 /* scope.removeHost = function(host_id, host_name) {
      HostsDelete({ scope: scope, "inventory_id": id, group_id: scope.group_id, host_id: host_id, host_name: host_name,
          request: 'remove' });
      } */

  scope.showEvents = function(host_name, last_job) {
      // When click on !Failed Events link, redirect to latest job/job_events for the host
      Rest.setUrl(last_job);
      Rest.get()
          .success( function(data, status, headers, config) {
              LoadBreadCrumbs({ path: '/jobs/' + data.id, title: data.name });
              $location.url('/jobs/' + data.id + '/job_events/?host=' + escape(host_name));
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                  { hdr: 'Error!', msg: 'Failed to lookup last job: ' + last_job + '. GET status: ' + status });
              });
      }
  
  scope.toggleAllHosts = function() {
      scope.hostDeleteHide = (scope.toggleAllFlag) ? false : true;
      for (var i=0; i < scope.hosts.length; i++) {
          scope.hosts[i].selected = scope.toggleAllFlag;
      }
      }

  scope.toggleOneHost = function() {
      var result = true;
      for (var i=0; i < scope.hosts.length; i++) {
          if (scope.hosts[i].selected) {
             result = false;
             break;   
          }
      }
      scope.hostDeleteHide = result;
      }

  // Respond to the scope.$emit from awTree directive
  scope.$on('refreshHost', function(e, group, title) {
      scope.groupTitle = title;
      scope.group_id = group;
      if (scope.group_id == null) {
         scope.hostAddHide = true;
         scope.hostCreateHide = true; 
         scope.hostDeleteHide = true;
      }
      else {
         scope.hostAddHide = false;
         scope.hostCreateHide = false; 
         scope.hostDeleteHide = false;
      }
      HostsReload({ scope: scope, inventory_id: scope['inventory_id'], group_id: group });
      });

}

InventoriesEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryForm', 
                            'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                            'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'LookUpInit', 'Prompt',
                            'OrganizationList', 'TreeInit', 'GetBasePath', 'GroupsList', 'GroupsAdd', 'GroupsEdit', 'LoadInventory',
                            'GroupsDelete', 'HostsList', 'HostsAdd', 'HostsEdit', 'HostsDelete', 'RefreshGroupName',
                            'ParseTypeChange', 'HostsReload', 'EditInventory', 'RefreshTree', 'LoadSearchTree'
                            ]; 
  
