/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
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
                          ClearScope, ProcessErrors, GetBasePath, Wait, Stream)
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
  
    if ($routeParams['name']) {
        scope[InventoryList.iterator + 'InputDisable'] = false;
        scope[InventoryList.iterator + 'SearchValue'] = $routeParams['name'];
        scope[InventoryList.iterator + 'SearchField'] = 'name';
        scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields['name'].label;
        scope[InventoryList.iterator + 'SearchSelectValue'] = null;
    }

    if ($routeParams['has_active_failures']) {
        scope[InventoryList.iterator + 'InputDisable'] = true;
        scope[InventoryList.iterator + 'SearchValue'] = $routeParams['has_active_failures'];
        scope[InventoryList.iterator + 'SearchField'] = 'has_active_failures';
        scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields['has_active_failures'].label;
        scope[InventoryList.iterator + 'SearchSelectValue'] = ($routeParams['has_active_failures'] == 'true') ? { value: 1 } : { value: 0 };
    }

    if ($routeParams['has_inventory_sources']) {
        scope[InventoryList.iterator + 'InputDisable'] = true;
        scope[InventoryList.iterator + 'SearchValue'] = $routeParams['has_inventory_sources'];
        scope[InventoryList.iterator + 'SearchField'] = 'has_inventory_sources';
        scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields['has_inventory_sources'].label;
        scope[InventoryList.iterator + 'SearchSelectValue'] = ($routeParams['has_inventory_sources'] == 'true') ? { value: 1 } : { value: 0 };
    }

    if ($routeParams['inventory_sources_with_failures']) {
        // pass a value of true, however this field actually contains an integer value
        scope[InventoryList.iterator + 'InputDisable'] = true;
        scope[InventoryList.iterator + 'SearchValue'] = $routeParams['inventory_sources_with_failures'];
        scope[InventoryList.iterator + 'SearchField'] = 'inventory_sources_with_failures';
        scope[InventoryList.iterator + 'SearchFieldLabel'] = InventoryList.fields['inventory_sources_with_failures'].label;
        scope[InventoryList.iterator + 'SearchType'] = 'gtzero';
    }

    scope.search(list.iterator);

    LoadBreadCrumbs();

    if (scope.removePostRefresh) {
       scope.removePostRefresh();
    }
    scope.removePostRefresh = scope.$on('PostRefresh', function() {
        //If we got here by deleting an inventory, stop the spinner and cleanup events
        Wait('stop');
        $('#prompt-modal').off();

        for (var i=0; i < scope.inventories.length; i++) {
            
            // Set values for Failed Hosts column
            scope.inventories[i].failed_hosts = scope.inventories[i].hosts_with_active_failures + ' / ' + scope.inventories[i].total_hosts;
            if (scope.inventories[i].hosts_with_active_failures > 0) {
               scope.inventories[i].failed_hosts_tip = "Contains " + scope.inventories[i].hosts_with_active_failures +
                   [ (scope.inventories[i].hosts_with_active_failures == 1) ? ' host' : ' hosts' ] + ' with job failures. Click to view the offending ' +
                   [ (scope.inventories[i].hosts_with_active_failures == 1) ? ' host' : ' hosts' ] + '.';
               scope.inventories[i].failed_hosts_link = '/#/inventories/' + scope.inventories[i].id + '/hosts?has_active_failures=true';
               scope.inventories[i].failed_hosts_class = 'true';
            }
            else {
               if (scope.inventories[i].total_hosts == 0) {
                  // no hosts
                  scope.inventories[i].failed_hosts_tip = "There are no hosts in this inventory. It's a sad empty shell. Click to view the hosts page " +
                      "and add a host.";
                  scope.inventories[i].failed_hosts_link = '/#/inventories/' + scope.inventories[i].id + '/hosts';
                  scope.inventories[i].failed_hosts_class = 'na';
               }
               else if (scope.inventories[i].total_hosts == 1) {
                  // on host with 0 failures
                  scope.inventories[i].failed_hosts_tip = "The 1 host found in this inventory is happy! There are no job failures." + 
                      " Click to view the host.";
                  scope.inventories[i].failed_hosts_link = '/#/inventories/' + scope.inventories[i].id + '/hosts';
                  scope.inventories[i].failed_hosts_class = 'false';
               }
               else {
                  // many hosts with 0 failures
                  scope.inventories[i].failed_hosts_tip = "All " + scope.inventories[i].total_hosts + " hosts are happy! There are no" + 
                      " job failures. Click to view the hosts.";
                  scope.inventories[i].failed_hosts_link = '/#/inventories/' + scope.inventories[i].id + '/hosts';
                  scope.inventories[i].failed_hosts_class = 'false';
               }
            }

            // Set values for Status column
            scope.inventories[i].status = scope.inventories[i].inventory_sources_with_failures + ' / ' + scope.inventories[i].total_inventory_sources; 
            if (scope.inventories[i].inventory_sources_with_failures > 0) {
               scope.inventories[i].status_tip = "Contains " + scope.inventories[i].inventory_sources_with_failures +
                   [ (scope.inventories[i].inventory_sources_with_failures == 1) ? ' group' : ' groups' ] + ' with inventory update failures. ' + 
                   'Click to view the ' +
                   [ (scope.inventories[i].inventory_sources_with_failures == 1) ? ' offending group.' : ' groups.' ];
               scope.inventories[i].status_link = '/#/inventories/' + scope.inventories[i].id + '/groups?status=failed';
               scope.inventories[i].status_class = 'failed'; 
            }
            else {
               if (scope.inventories[i].total_inventory_sources == 0) {
                  // no groups are reporting a source
                  scope.inventories[i].status_tip = "Does not have an external inventory source. Click to view groups and " +
                      "and add an inventory source.";
                  scope.inventories[i].status_link = '/#/inventories/' + scope.inventories[i].id + '/groups';
                  scope.inventories[i].status_class = 'na';
               }
               else if (scope.inventories[i].total_inventory_sources == 1) {
                  // on host with 0 failures
                  scope.inventories[i].status_tip = "The 1 group with an inventory source is happy!. No updates have failed." + 
                      " Click to view the group.";
                  scope.inventories[i].status_link = '/#/inventories/' + scope.inventories[i].id + '/groups?has_external_source=true';
                  scope.inventories[i].status_class = 'successful';
               }
               else {
                  // many hosts with 0 failures
                  scope.inventories[i].status_tip = scope.inventories[i].total_inventory_sources + " groups external inventory sources are happy! " +
                      " No updates have failed. Click to view the groups.";
                  scope.inventories[i].status_link = '/#/inventories/' + scope.inventories[i].id + '/groups?has_external_source=true';
                  scope.inventories[i].status_class = 'successful';
               }  
            }

        }
        });
    
    scope.showActivity = function() { Stream(); }

    scope.addInventory = function() {
        $location.path($location.path() + '/add');
        }

    scope.editInventory = function(id) {
        $location.path($location.path() + '/' + id);
        }
 
    scope.deleteInventory = function(id, name) {
       
        var action = function() {
            var url = defaultUrl + id + '/';
            $('#prompt-modal').on('hidden.bs.modal', function() {
                Wait('start');
                });
            $('#prompt-modal').modal('hide');
            Rest.setUrl(url);
            Rest.destroy()
                .success( function(data, status, headers, config) {
                    scope.search(list.iterator); 
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
        $location.url('/jobs/?inventory__int=' + id);
        }

     scope.viewFailedJobs = function(id) {
        $location.url('/jobs/?inventory__int=' + id + '&status=failed');
        }
}

InventoriesList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'InventoryList', 'GenerateList', 
                            'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
                            'GetBasePath', 'Wait', 'Stream' ];


function InventoriesAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, InventoryForm, 
                         GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
                         GenerateList, OrganizationList, SearchInit, PaginateInit, LookUpInit, GetBasePath,
                         ParseTypeChange, Wait) 
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
       generator.clearApiErrors();
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

           Rest.setUrl(defaultUrl);
           Rest.post(data)
               .success( function(data, status, headers, config) {
                   var inventory_id = data.id;
                   if (scope.inventory_variables) {
                      Rest.setUrl(data.related.variable_data);
                      Rest.put(json_data)
                          .success( function(data, status, headers, config) {
                              Wait('stop');
                              $location.path('/inventories/' + inventory_id + '/');           
                              })
                          .error( function(data, status, headers, config) {
                              Wait('stop');
                              ProcessErrors(scope, data, status, form,
                                 { hdr: 'Error!', msg: 'Failed to add inventory varaibles. PUT returned status: ' + status });
                          });
                   }
                   else {
                      Wait('stop');
                      $location.path('/inventories/' + inventory_id + '/');
                   }
                   })
               .error( function(data, status, headers, config) {
                   Wait('stop');
                   ProcessErrors(scope, data, status, form,
                       { hdr: 'Error!', msg: 'Failed to add new inventory. Post returned status: ' + status });
                   });
       }
       catch(err) {
           Wait('stop');
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
                           'OrganizationList', 'SearchInit', 'PaginateInit', 'LookUpInit', 'GetBasePath', 'ParseTypeChange', 'Wait'
                           ]; 



function InventoriesEdit ($scope, $location, $routeParams, $compile, GenerateList, ClearScope, InventoryGroups, InventoryHosts, BuildTree, Wait, 
                          GetSyncStatusMsg, InjectHosts, HostsReload, GroupsAdd, GroupsEdit, GroupsDelete, Breadcrumbs, LoadBreadCrumbs, Empty, 
                          Rest, ProcessErrors, InventoryUpdate, Alert, ToggleChildren, ViewUpdateStatus, GroupsCancelUpdate) 
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.

    var generator = GenerateList;
    var list = InventoryGroups;
    var base = $location.path().replace(/^\//,'').split('/')[0];  
    
    $scope.inventory_id = $routeParams.inventory_id;
    
    LoadBreadCrumbs();

    if ($scope.removeGroupTreeLoaded) {
        $scope.removeGroupTreeLoaded();
    }
    $scope.removeGroupTreeLoaded = $scope.$on('groupTreeLoaded', function(e, inventory_name, groups) {
        // After the tree data loads, generate the groups list
        // Add breadcrumbs
        var e = angular.element(document.getElementById('breadcrumbs'));
        e.html(Breadcrumbs({ list: list, mode: 'edit' }));
        $compile(e)($scope);
        
        // Add groups view
        generator.inject(list, { mode: 'edit', id: 'groups-container', breadCrumbs: false, searchSize: 'col-lg-5 col-md-5 col-sm-5' });
        $scope.groups = groups;
        $scope.inventory_name = inventory_name;

        // Default the selected group to the first node
        if ($scope.groups.length > 0) {
            $scope.selected_tree_id = $scope.groups[0].id;
            $scope.selected_group_id = $scope.groups[0].group_id;
            $scope.groups[0].selected_class = 'selected';
            $scope.groups[0].active_class = 'active-row';
            $scope.selected_group_name = $scope.groups[0].name;
        }
        else {
            $scope.selected_tree_id = null;
            $scope.selected_group_id = null;
        } 

        // Add hosts view
        $scope.show_failures = false;
        InjectHosts({ scope: $scope, inventory_id: $scope.inventory_id, tree_id: $scope.selected_tree_id, group_id: $scope.selected_group_id }); 
        });

    if ($scope.removeGroupTreeRefreshed) {
        $scope.removeGroupTreeRefreshed();
    }
    $scope.removeGroupTreeRefreshed = $scope.$on('groupTreeRefreshed', function(e, inventory_name, groups, emit) {
        // Called after tree data is reloaded on refresh button click.
        // Reselect the preveiously selected group node, causing host view to refresh.
        $scope.showHosts($scope.selected_tree_id, $scope.selected_group_id, false, emit);
        });

    if ($scope.removeGroupDeleteCompleted) {
        $scope.removeGroupDeleteCompleted();
    }
    $scope.removeGroupDeleteCompleted = $scope.$on('groupDeleteCompleted', function(e) {
        // Group was deleted. Now we need to refresh the group view.
        BuildTree({ scope: $scope, inventory_id: $scope.inventory_id, refresh: true });
        });
    
    $scope.showHosts = function(tree_id, group_id, show_failures, emit) {
        // Clicked on group
        if (tree_id !== null) {
            Wait('start');
            $scope.selected_tree_id = tree_id; 
            $scope.selected_group_id = group_id;
            $scope.hosts = [];
            $scope.show_failures = show_failures;  // turn on failed hosts filter in hosts view
            for (var i=0; i < $scope.groups.length; i++) {
                if ($scope.groups[i].id == tree_id) {
                    $scope.groups[i].selected_class = 'selected';
                    $scope.groups[i].active_class = 'active-row';
                    $scope.selected_group_name = $scope.groups[i].name;
                }
                else {
                    $scope.groups[i].selected_class = '';
                    $scope.groups[i].active_class = '';
                }
            }
            HostsReload({ scope: $scope, group_id: group_id, tree_id: tree_id, inventory_id: $scope.inventory_id, emit: emit });
        }
        }

    $scope.createGroup = function() {
        GroupsAdd({ scope: $scope, inventory_id: $scope.inventory_id, group_id: $scope.selected_group_id  });
        }
        
    $scope.editGroup = function(group_id) {
        GroupsEdit({ scope: $scope, inventory_id: $scope.inventory_id, group_id: group_id });
        }

    // Launch inventory sync
    $scope.updateGroup = function(id) {
        for (var i=0; i < $scope.groups.length; i++) {
            if ($scope.groups[i].id == id) {
                if (Empty($scope.groups[i].source)) {
                    // if no source, do nothing. 
                }
                else if ($scope.groups[i].status == 'updating') {
                    Alert('Update in Progress', 'The inventory update process is currently running for group <em>' +
                        $scope.groups[i].name + '</em>. Use the Refresh button to monitor the status.', 'alert-info'); 
                }
                else {
                    Wait('start');
                    Rest.setUrl($scope.groups[i].related.inventory_source);
                    Rest.get()
                        .success( function(data, status, headers, config) {
                            InventoryUpdate({
                                scope: $scope, 
                                url: data.related.update,
                                group_name: data.summary_fields.group.name, 
                                group_source: data.source
                                });
                            })
                        .error( function(data, status, headers, config) {
                            Wait('stop');
                            ProcessErrors(scope, data, status, form,
                                { hdr: 'Error!', msg: 'Failed to retrieve inventory source: ' + $scope.groups[i].related.inventory_source + 
                                ' POST returned status: ' + status });
                            });
                }
                break;
            }
        }      
        }

    $scope.cancelUpdate = function(id) {
        GroupsCancelUpdate({ scope: $scope, id: id });
        }
    
    $scope.toggle = function(id) {
        // Expand/collapse nodes
        ToggleChildren({ scope: $scope, list: list, id: id });
        }

    $scope.refreshGroups = function(emit) {
        // Refresh the tree data when refresh button cicked
        // Pass a string label value, if you want to attach scope.$on() to the completion of the refresh  
        BuildTree({ scope: $scope, inventory_id: $scope.inventory_id, refresh: true, emit: emit });
        }

    $scope.viewUpdateStatus = function(id) {
        ViewUpdateStatus({ scope: $scope, tree_id: id });
        }

    $scope.deleteGroup = function(id) {
        GroupsDelete({ scope: $scope, tree_id: id, inventory_id: $scope.inventory_id });
        }
    
    //Load tree data for the first time
    BuildTree({ scope: $scope, inventory_id: $scope.inventory_id, refresh: false });

}

InventoriesEdit.$inject = [ '$scope', '$location', '$routeParams', '$compile', 'GenerateList', 'ClearScope', 'InventoryGroups', 'InventoryHosts', 
                            'BuildTree', 'Wait', 'GetSyncStatusMsg', 'InjectHosts', 'HostsReload', 'GroupsAdd', 'GroupsEdit', 'GroupsDelete',
                            'Breadcrumbs', 'LoadBreadCrumbs', 'Empty', 'Rest', 'ProcessErrors', 'InventoryUpdate', 'Alert', 'ToggleChildren',
                            'ViewUpdateStatus', 'GroupsCancelUpdate'
                            ]; 
  
