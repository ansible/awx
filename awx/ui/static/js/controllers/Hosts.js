/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
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
                         HostsReload, LoadSearchTree, EditHostGroups) 
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

   if (scope.loadBreadCrumbsRemove) {
      scope.loadBreadCrumbsRemove();
   }
   scope.loadBreadCrumbsRemove = scope.$on('hostTabInit', function(e, inventory_name) {
       LoadBreadCrumbs({ path: '/inventories/' + id, title: inventory_name });
       });

   LoadSearchTree({ scope: scope, inventory_id: scope['inventory_id'] });
   
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

  // Respond to the scope.$emit from awTree directive
  if (scope.refreshHostRemove) {
     scope.refreshHostRemove();
  }
  scope.refreshHostRemove = scope.$on('refreshHost', function(e, group, title) {
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
      scope['hostDeleteDisabled'] = true; 
      scope['hostDeleteDisabledClass'] = 'disabled';
      HostsReload({ scope: scope, inventory_id: scope['inventory_id'], group_id: group });
      });

}

InventoryHosts.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'InventoryHostsForm', 
                            'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                            'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'LookUpInit', 'Prompt',
                            'GetBasePath', 'HostsList', 'HostsAdd', 'HostsEdit', 'HostsDelete',
                            'HostsReload', 'LoadSearchTree', 'EditHostGroups'
                            ]; 
  
