/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Hosts.js
 *  
 *  Controller functions for the Hosts model.
 *
 */

'use strict';

function InventoryHosts ($scope, $rootScope, $compile, $location, $log, $routeParams, InventoryHostsForm,
                         GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, 
                         RelatedPaginateInit, ReturnToCaller, ClearScope, LookUpInit, Prompt,
                         GetBasePath, HostsList, HostsAdd, HostsEdit, HostsDelete,
                         HostsReload, BuildTree, EditHostGroups, InventoryHostsHelp, HelpDialog, Wait,
                         ToggleHostEnabled, Stream)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.

    var generator = GenerateForm;
    var form = InventoryHostsForm;
    var defaultUrl=GetBasePath('inventory');
    var scope = generator.inject(form, {mode: 'edit', related: true, buildTree: true});
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var id = $routeParams.inventory_id;
    
    scope['inventory_id'] = id;
    scope['hostAddHide'] = true;
    scope['hostCreateHide'] = true;
    scope['hosts'] = null;
    scope['helpCount'] = 0;

    // buildAllGroups emits from TreeSelector.js after the inventory object is ready
    if (scope.loadBreadCrumbsRemove) {
        scope.loadBreadCrumbsRemove();
    }
    scope.loadBreadCrumbsRemove = scope.$on('buildAllGroups', function(e, inventory_name) {
        LoadBreadCrumbs({ path: '/inventories/' + id, title: inventory_name });
        });

    scope.showActivity = function() { Stream(); }

    scope.filterHosts = function() {
        HostsReload({ scope: scope, inventory_id: scope['inventory_id'], group_id: scope['group_id'] });
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
    
    scope.editGroups = function() {
        $location.path('/inventories/' + scope.inventory_id + '/groups');
        } 

    scope.editHostGroups = function(host_id) {
        EditHostGroups({ inventory_id: id, host_id: host_id });
        }

    scope.deleteHost = function(host_id, host_name) {
        HostsDelete({ scope: scope, "inventory_id": id, group_id: scope.group_id, host_id: host_id, host_name: host_name,
            request: 'delete' });
        }
  
    scope.viewJobs = function(last_job) {
        $location.url('/jobs/?id__int=' + last_job );
        }
 
    scope.allJobs = function(id) {
        $location.url('/jobs/?job_host_summaries__host=' + id);
        } 
    
    scope.toggle_host_enabled = function(id, sources) { ToggleHostEnabled(id, sources, scope); }

    scope.allHostSummaries = function(id, name, inventory_id) {
        LoadBreadCrumbs({ path: '/hosts/' + id, title: name, altPath: '/inventories/' + inventory_id + '/hosts', 
            inventory_id: inventory_id });
        $location.url('/hosts/' + id + '/job_host_summaries/?inventory=' + inventory_id);
        } 

    scope.viewLastEvents = function(host_id, last_job, host_name, last_job_name) {
        // Choose View-> Latest job events
        LoadBreadCrumbs({ path: '/jobs/' + last_job, title: last_job_name });
        $location.url('/jobs/' + last_job + '/job_events/?host=' + escape(host_name));
        }
  
    scope.viewLastSummary = function(host_id, last_job, host_name, last_job_name) {
        // Choose View-> Latest job events
        LoadBreadCrumbs({ path: '/jobs/' + last_job, title: last_job_name });
        $location.url('/jobs/' + last_job + '/job_host_summaries/?host=' + escape(host_name));
        }

    if (scope.removeShowHelp) {
       scope.removeShowHelp();
    }
    scope.removeShowHelp = scope.$on('ShowHelp', function() {
        // Force display fo help tooltip when no groups exist
        $('#hosts-page-help').focus();
        });

    scope.showHelp = function() {
        // Display help dialog
        $('.btn').blur();  //remove focus from the help button and all buttons
                           //this stops the tooltip from continually displaying
        HelpDialog({ defn: InventoryHostsHelp });
        }

    // Refresh host is emitted each time a group on the selector tree is clicked
    if (scope.refreshHostRemove) {
       scope.refreshHostRemove();
    } 
    scope.refreshHostRemove = scope.$on('refreshHost', function(e, id, group, title) {
        scope.groupTitle = title;
        scope.group_id = group;
        scope.helpCount++;
        if (scope.group_id == null) {
            scope.groupTitle = 'All Hosts';
            scope.hostAddHide = true;
            scope.hostCreateHide = true; 
            scope.hostDeleteHide = true;
        }
        else {
            scope.hostAddHide = false;
            scope.hostCreateHide = false; 
            scope.hostDeleteHide = false;
        }
        scope['hostDeleteDisabled'] = true; 
        scope['hostDeleteDisabledClass'] = 'disabled';
        HostsReload({ scope: scope, inventory_id: scope['inventory_id'], group_id: group });
        });

    // Load the tree. See TreeSelector.js
    var group_id = ($routeParams['group'] !== undefined) ? $routeParams['group'] : null;
    if (group_id !== null) {
        // group was passed as a search parameter. load the tree with the group selected.
        BuildTree({
            scope: scope,
            inventory_id: id,
            emit_on_select: 'refreshHost',
            target_id: 'search-tree-container',
            refresh: true,
            group_id: group_id
            });
    }
    else {
        BuildTree({
            scope: scope,
            inventory_id: id,
            emit_on_select: 'refreshHost',
            target_id: 'search-tree-container'
            });
    }
}

InventoryHosts.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryHostsForm', 
                            'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                            'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'LookUpInit', 'Prompt',
                            'GetBasePath', 'HostsList', 'HostsAdd', 'HostsEdit', 'HostsDelete',
                            'HostsReload', 'BuildTree', 'EditHostGroups', 'InventoryHostsHelp', 'HelpDialog', 'Wait',
                            'ToggleHostEnabled', 'Stream'
                            ]; 
  
