/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Groups.js
 *  
 *  Controller functions for the Groups model.
 *
 */

function InventoryGroups ($scope, $rootScope, $compile, $location, $log, $routeParams, InventoryGroupsForm,
                          GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope, Prompt,
                          BuildTree, GetBasePath, GroupsList, GroupsAdd, GroupsEdit, LoadInventory,
                          GroupsDelete, RefreshGroupName, EditInventory, InventoryStatus) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var generator = GenerateForm;
   var form = InventoryGroupsForm;
   var defaultUrl=GetBasePath('inventory');
   
   $('#tree-view').empty();
   var scope = generator.inject(form, { mode: 'edit', related: true, buildTree: true });
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var id = $routeParams.inventory_id;
   
   scope.grpBtnDisable = false;
   scope['inventory_id'] = id;
   
   // Retrieve each related sets and any lookups
   if (scope.inventoryLoadedRemove) {
      scope.inventoryLoadedRemove();
   }
   scope.inventoryLoadedRemove = scope.$on('inventoryLoaded', function() {
       LoadBreadCrumbs({ path: '/inventories/' + id, title: scope.inventory_name });
       BuildTree({
           scope: scope,
           inventory_id: id,
           emit_on_select: 'NodeSelect',
           target_id: 'search-tree-container',
           moveable: true
           });
       if (!scope.$$phase) {
          scope.$digest();
       }
       });

   LoadInventory({ scope: scope, doPostSteps: false });

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
  
  scope.$on('NodeSelect', function(e, id, group_id, name) {
      
      // Respond to user clicking on a tree node

      var node = $('#' + id);
      var parent = node.parent().parent();
      var type = (group_id == null) ? 'inventory' : 'group';
      var url;
      
      /*if ($rootScope.timer) {
         // Kill any lingering timers from the inventory summary page
         clearInterval($rootScope.timer);
         $rootScope.timer = null;
      }*/

      scope['selectedNode'] = node;
      scope['selectedNodeName'] = name
      scope['grpBtnDisable'] = false;
      scope['flashMessage'] = null;
      scope['groupUpdateHide'] = true;

      //$('#tree-view').jstree('open_node',node);
      
      if (type == 'group') {
         //url = node.attr('all');
         scope.groupAddHide = false;
         scope.groupCreateHide = false;
         scope.groupEditHide = false;
         scope.inventoryEditHide = true;
         scope.groupDeleteHide = false;
         scope.createButtonShow = true;
         scope.group_id = group_id;
         scope.addGroupHelp = "Copy an existing group into " + name;
         scope.createGroupHelp = "Create a new group, adding it to " + name;
         scope.updateGroupHelp = "Start the inventory update process, refreshing " + name;
         if (parent.attr('id') == 'inventory-root-node') {
            scope.deleteGroupHelp = "Remove " + name + " from " + parent.attr('data-name') + 
             " Inventory. Any hosts will still be available in All Hosts."; 
         }
         else {
            scope.deleteGroupHelp = "Remove " + name + " from " + parent.attr('data-name') + 
             ". Any hosts will still be available in " + parent.attr('name') + " and All Hosts."; 
         }
         
         // Load the form
         GroupsEdit({ "inventory_id": scope['inventory_id'], group_id: scope['group_id'] });

         // Slide in the group properties form
         $('#tree-form').show();
         $('input:first').focus();
      }
      else if (type == 'inventory') {
         //url = node.attr('hosts');
         scope.groupAddHide = true;
         scope.groupCreateHide = false; 
         scope.groupEditHide =true;
         scope.inventoryEditHide=false;
         scope.groupDeleteHide = true;
         scope.createButtonShow = false;
         scope.group_id = null;
         scope.inventory_name = name;
         InventoryStatus({ scope: scope });
         $('#tree-form').show();
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
      // Slide in the group properties form
      $('#tree-form').show('slide', {direction: 'up'}, 500, function() {
          // Remove any tooltips that might be lingering
          $('.tooltip').each( function(index) {
              $(this).remove();
              });
          $('.popover').each(function(index) {
              // remove lingering popover <div>. Seems to be a bug in TB3 RC1
              $(this).remove();
              });
          // Set the focust to the first form field
          $('input:first').focus();
          });   
      
      // Disable all the group related buttons
      scope.grpBtnDisable = false;
          
      }

  scope.closeForm = function() {
      // Slide in the group properties form
      $('#tree-form').hide('slide',{ direction: 'right' }, 500, function() { $('#tree-form').empty(); });
      scope.grpBtnDisable = false;
      }

  scope.editInventory = function() {
      EditInventory({ scope: scope, inventory_id: id });
      }

  scope.deleteGroup = function() {
      GroupsDelete({ scope: scope, "inventory_id": id, group_id: scope.group_id });
      }
  
  scope.editHosts = function() {
      $location.path('/inventories/' + scope.inventory_id + '/hosts');
      }
}

InventoryGroups.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryGroupsForm',
                            'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'Prompt',
                            'BuildTree', 'GetBasePath', 'GroupsList', 'GroupsAdd', 'GroupsEdit', 'LoadInventory',
                            'GroupsDelete', 'RefreshGroupName', 'EditInventory', 'InventoryStatus'
                            ]; 
  