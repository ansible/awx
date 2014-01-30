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
                          ClearScope, ProcessErrors, GetBasePath, Wait, Stream, EditInventoryProperties)
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
            //scope.inventories[i].failed_hosts = scope.inventories[i].hosts_with_active_failures + ' / ' + scope.inventories[i].total_hosts;
            
            if (scope.inventories[i].hosts_with_active_failures > 0) {
               scope.inventories[i].failed_hosts_tip = scope.inventories[i].hosts_with_active_failures +
                   ( (scope.inventories[i].hosts_with_active_failures == 1) ? ' host' : ' hosts' ) + ' with job failures. Click to view details.';
               scope.inventories[i].failed_hosts_link = '/#/inventories/' + scope.inventories[i].id + '/';
               scope.inventories[i].failed_hosts_class = 'true';
            }
            else {
               if (scope.inventories[i].total_hosts == 0) {
                  // no hosts
                  scope.inventories[i].failed_hosts_tip = "No hosts defined. Click to add.";
                  scope.inventories[i].failed_hosts_link = '/#/inventories/' + scope.inventories[i].id + '/';
                  scope.inventories[i].failed_hosts_class = 'na';
               }
               else {
                  // many hosts with 0 failures
                  scope.inventories[i].failed_hosts_tip = scope.inventories[i].total_hosts + 
                      ( (scope.inventories[i].total_hosts > 1) ? ' hosts' : ' host' ) + " with no job failures. Click to view details.";
                  scope.inventories[i].failed_hosts_link = '/#/inventories/' + scope.inventories[i].id + '/';
                  scope.inventories[i].failed_hosts_class = 'false';
               }
            }

            // Set values for Status column
            scope.inventories[i].status = scope.inventories[i].inventory_sources_with_failures + ' / ' + scope.inventories[i].total_inventory_sources; 
            if (scope.inventories[i].inventory_sources_with_failures > 0) {
               scope.inventories[i].status_tip = scope.inventories[i].inventory_sources_with_failures + ' cloud ' +
                   ( (scope.inventories[i].inventory_sources_with_failures == 1) ? 'source' : 'sources' ) + 
                   ' with failures. Click to view details.';
               scope.inventories[i].status_link = '/#/inventories/' + scope.inventories[i].id + '/';
               scope.inventories[i].status_class = 'failed'; 
            }
            else {
               if (scope.inventories[i].total_inventory_sources == 0) {
                  // no groups are reporting a source
                  scope.inventories[i].status_tip = "Not synced with a cloud source. Click to edit.";
                  scope.inventories[i].status_link = '/#/inventories/' + scope.inventories[i].id + '/';
                  scope.inventories[i].status_class = 'na';
               }
               else {
                  // many hosts with 0 failures
                  scope.inventories[i].status_tip = scope.inventories[i].total_inventory_sources + 
                      ' cloud ' + ( (scope.inventories[i].total_inventory_sources > 1) ? 'sources' : 'source' ) + 
                      ' with no failures. Click to view details.';
                  scope.inventories[i].status_link = '/#/inventories/' + scope.inventories[i].id + '/';
                  scope.inventories[i].status_class = 'successful';
               }  
            }

        }
        });

    if (scope.removeRefreshInventories) {
        scope.removeRefreshInventories();
    }
    scope.removeRefreshInventories = scope.$on('RefreshInventories', function() {
        // Reflect changes after inventory properties edit completes
        scope.search(list.iterator);
        });
    
    scope.showActivity = function() { Stream({ scope: scope }); }

    scope.editInventoryProperties = function(inventory_id) { 
        EditInventoryProperties({ scope: scope, inventory_id: inventory_id });
        }

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
                            'GetBasePath', 'Wait', 'Stream', 'EditInventoryProperties'];


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
                          Rest, ProcessErrors, InventoryUpdate, Alert, ToggleChildren, ViewUpdateStatus, GroupsCancelUpdate, Find,
                          HostsCreate, EditInventoryProperties, HostsEdit, HostsDelete, ToggleHostEnabled, CopyMoveGroup, CopyMoveHost,
                          Stream, GetBasePath, ShowJobSummary, ApplyEllipsis, WatchInventoryWindowResize, HelpDialog, InventoryGroupsHelp,
                          Store) 
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.

    var generator = GenerateList;
    var list = InventoryGroups;
    var base = $location.path().replace(/^\//,'').split('/')[0];  
    
    $scope.inventory_id = $routeParams.inventory_id;
    
    LoadBreadCrumbs({ path: $location.path(), title: '{{ inventory_name }}' });

    // After the tree data loads for the first time, generate the groups and hosts lists
    if ($scope.removeGroupTreeLoaded) {
        $scope.removeGroupTreeLoaded();
    }
    $scope.removeGroupTreeLoaded = $scope.$on('GroupTreeLoaded', function(e, inventory_name, groups) {
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
        
        // As the window shrinks and expands, apply ellipsis
        setTimeout(function() {
            // Hack to keep group name from slipping to a new line
            $('#groups_table .name-column').each( function() {
                var td_width = $(this).width();
                var level_width = $(this).find('.level').width();
                var level_padding = parseInt($(this).find('.level').css('padding-left').replace(/px/,''));
                var level = level_width + level_padding;
                var pct = ( 100 - Math.ceil((level / td_width)*100) ) + '%';
                $(this).find('.group-name').css({ width: pct });
                });
            ApplyEllipsis('#groups_table .group-name a');
            ApplyEllipsis('#hosts_table .host-name a');
            }, 2500); //give the window time to display
        WatchInventoryWindowResize();
        
        var inventoryAutoHelp = Store('inventoryAutoHelp');
        if (inventoryAutoHelp !== 'off' && $scope.autoShowGroupHelp) {
            $scope.showGroupHelp({ autoShow: true });
        }

        });
   

    // Called after tree data is reloaded on refresh button click.
    if ($scope.removeGroupTreeRefreshed) {
        $scope.removeGroupTreeRefreshed();
    }
    $scope.removeGroupTreeRefreshed = $scope.$on('GroupTreeRefreshed', function(e, inventory_name, groups) {
        // Reapply ellipsis to groups
        setTimeout(function() { ApplyEllipsis('#groups_table .group-name a'); }, 2500);
        // Reselect the preveiously selected group node, causing host view to refresh.
        $scope.showHosts($scope.selected_tree_id, $scope.selected_group_id, false);
        });
    
    // Group was deleted. Now we need to refresh the group view.
    if ($scope.removeGroupDeleteCompleted) {
        $scope.removeGroupDeleteCompleted();
    }
    $scope.removeGroupDeleteCompleted = $scope.$on('GroupDeleteCompleted', function(e) {
        $scope.selected_tree_id = 1;
        $scope.selected_group_id = null;
        BuildTree({ scope: $scope, inventory_id: $scope.inventory_id, refresh: true });
        });

    // Respond to a group drag-n-drop
    if ($scope.removeCopMoveGroup) {
        $scope.removeCopyMoveGroup();
    }
    $scope.removeCopyMoveGroup = $scope.$on('CopyMoveGroup', function(e, inbound_tree_id, target_tree_id) {
        CopyMoveGroup({ scope: $scope, target_tree_id: target_tree_id, inbound_tree_id: inbound_tree_id });
        });

    // Respond to a host drag-n-drop
    if ($scope.removeCopMoveHost) {
        $scope.removeCopyMoveHost();
    }
    $scope.removeCopyMoveHost = $scope.$on('CopyMoveHost', function(e, target_tree_id, host_id) {
        CopyMoveHost({ scope: $scope, target_tree_id: target_tree_id, host_id: host_id });
        });

    $scope.showHosts = function(tree_id, group_id, show_failures) {
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
            HostsReload({ scope: $scope, group_id: group_id, tree_id: tree_id, inventory_id: $scope.inventory_id });
        }
        else {
            Wait('stop');
        }
        }

    $scope.createGroup = function() {
        GroupsAdd({ scope: $scope, inventory_id: $scope.inventory_id, group_id: $scope.selected_group_id  });
        }
        
    $scope.editGroup = function(group_id, tree_id) {
        GroupsEdit({ scope: $scope, inventory_id: $scope.inventory_id, group_id: group_id, tree_id: tree_id, groups_reload: true });
        }

    // Launch inventory sync
    $scope.updateGroup = function(id) {
        var group = Find({ list: $scope.groups, key: 'id', val: id});
        if (group) {
            if (Empty(group.source)) {
                // if no source, do nothing. 
            }
            else if (group.status == 'updating') {
                Alert('Update in Progress', 'The inventory update process is currently running for group <em>' +
                    $scope.groups[i].name + '</em>. Use the Refresh button to monitor the status.', 'alert-info'); 
            }
            else {
                Wait('start');
                Rest.setUrl(group.related.inventory_source);
                Rest.get()
                    .success( function(data, status, headers, config) {
                        InventoryUpdate({
                            scope: $scope, 
                            url: data.related.update,
                            group_name: data.summary_fields.group.name, 
                            group_source: data.source,
                            tree_id: group.id,
                            group_id: group.group_id
                            });
                        })
                    .error( function(data, status, headers, config) {
                        Wait('stop');
                        ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to retrieve inventory source: ' + group.related.inventory_source + 
                            ' POST returned status: ' + status });
                        });
            }
        }      
        }

    $scope.cancelUpdate = function(tree_id) {
        GroupsCancelUpdate({ scope: $scope, tree_id: tree_id });
        }
    
    $scope.toggle = function(tree_id) {
        // Expand/collapse nodes
        ToggleChildren({ scope: $scope, list: list, id: tree_id });
        }

    $scope.refreshGroups = function(tree_id, group_id) {
        // Refresh the tree data when refresh button cicked
        if (tree_id) {
            $scope.selected_tree_id = tree_id;
            $scope.selected_group_id = group_id;
        }
        BuildTree({ scope: $scope, inventory_id: $scope.inventory_id, refresh: true });
        }

    $scope.viewUpdateStatus = function(tree_id, group_id) {
        ViewUpdateStatus({ scope: $scope, tree_id: tree_id, group_id: group_id });
        }

    $scope.deleteGroup = function(tree_id, group_id) {
        GroupsDelete({ scope: $scope, tree_id: tree_id, group_id: group_id, inventory_id: $scope.inventory_id });
        }

    $scope.createHost = function() {
        HostsCreate({ scope: $scope });
        }
    
    $scope.editInventoryProperties = function() { 
        EditInventoryProperties({ scope: $scope, inventory_id: $scope.inventory_id });
        }

    $scope.editHost = function(host_id) {
        HostsEdit({ scope: $scope, host_id: host_id, inventory_id: $scope.inventory_id });
        }

    $scope.deleteHost = function(host_id, host_name) {
        HostsDelete({ scope: $scope, host_id: host_id, host_name: host_name });
        }

    $scope.toggleHostEnabled = function(host_id, external_source) {
        ToggleHostEnabled({ scope: $scope, host_id: host_id, external_source: external_source });
        }

    $scope.showGroupActivity = function() { 
        var url, title, group;
        if ($scope.selected_group_id) {
            group = Find({ list: $scope.groups, key: 'id', val: $scope.selected_tree_id });
            url = GetBasePath('activity_stream') + '?group__id=' + $scope.selected_group_id;
            title = 'Showing all activities for group ' + group.name;
        }
        else {
            title = 'Showing all activities for all ' + $scope.inventory_name + ' groups';
            url = GetBasePath('activity_stream') + '?group__inventory__id=' + $scope.inventory_id;
        }
        Stream({ scope: $scope, inventory_name: $scope.inventory_name, url: url, title: title });
        }
    
    $scope.showHostActivity = function() { 
        var url, title;
        title = 'Showing all activities for all ' + $scope.inventory_name + ' hosts';
        url = GetBasePath('activity_stream') + '?host__inventory__id=' + $scope.inventory_id;
        Stream({ scope: $scope, inventory_name: $scope.inventory_name, url: url, title: title });
        }

    $scope.showJobSummary = function(job_id) { 
        ShowJobSummary({ job_id: job_id });
        }

    $scope.showGroupHelp = function(params) {
        var opts = { defn: InventoryGroupsHelp };
        if (params) {
            opts.autoShow = params.autoShow || false;
        }
        HelpDialog(opts);
        }

    //Load tree data for the first time
    BuildTree({ scope: $scope, inventory_id: $scope.inventory_id, refresh: false });

    }

InventoriesEdit.$inject = [ '$scope', '$location', '$routeParams', '$compile', 'GenerateList', 'ClearScope', 'InventoryGroups', 'InventoryHosts', 
                            'BuildTree', 'Wait', 'GetSyncStatusMsg', 'InjectHosts', 'HostsReload', 'GroupsAdd', 'GroupsEdit', 'GroupsDelete',
                            'Breadcrumbs', 'LoadBreadCrumbs', 'Empty', 'Rest', 'ProcessErrors', 'InventoryUpdate', 'Alert', 'ToggleChildren',
                            'ViewUpdateStatus', 'GroupsCancelUpdate', 'Find', 'HostsCreate', 'EditInventoryProperties', 'HostsEdit', 
                            'HostsDelete', 'ToggleHostEnabled', 'CopyMoveGroup', 'CopyMoveHost', 'Stream', 'GetBasePath', 'ShowJobSummary',
                            'ApplyEllipsis', 'WatchInventoryWindowResize', 'HelpDialog', 'InventoryGroupsHelp', 'Store'
                            ]; 
  
