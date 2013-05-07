/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Groups.js
 *  
 *  Controller functions for Group model.
 *
 */

'use strict';

function GroupsList ($scope, $rootScope, $location, $log, $routeParams, Rest, 
                     Alert, GroupList, GenerateList, LoadBreadCrumbs, Prompt, SearchInit,
                     PaginateInit, ReturnToCaller, ClearScope, ProcessErrors)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.

    var list = GroupList;
    var defaultUrl = '/api/v1/inventories/' + $routeParams.id + '/groups/';
    var view = GenerateList;
    var paths = $location.path().replace(/^\//,'').split('/');
    var scope = view.inject(GroupList, { mode: 'edit' });               // Inject our view
    scope.selected = [];
  
    SearchInit({ scope: scope, set: 'groups', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();

    scope.addGroup = function() {
       $location.path($location.path() + '/add');
       }

    scope.editGroup = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteGroup = function(id, name) {
       
       var action = function() {
           var url = defaultUrl;
           Rest.setUrl(url);
           Rest.post({ id: id, disassociate: 1 })
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
                body: 'Are you sure you want to delete group' + name + '?',
                action: action
                });
       }

}

GroupsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'GroupList', 'GenerateList', 
                       'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'LookUpInventoryInit'];


function GroupsAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, GroupForm, 
                   GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller,
                   ClearScope, LookUpInventoryInit) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var defaultUrl = '/api/v1/inventories/';
   var form = GroupForm;
   var generator = GenerateForm;
   var scope = generator.inject(form, {mode: 'add', related: false});
   generator.reset();
   var master={};

   LoadBreadCrumbs();

   LookUpInventoryInit({ scope: scope });

   // Load inventory lookup value
   var url = defaultUrl + $routeParams.id + '/';
   Rest.setUrl(url);
   Rest.get()
       .success( function(data, status, headers, config) {
           scope['inventory'] = data.id;
           master['inventory'] = data.id;
           scope['inventory_name'] = data.name;
           master['inventory_name'] = data.name;
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, null,
                         { hdr: 'Error!', msg: 'Failed to retrieve: ' + url + '. GET status: ' + status });
           });

   // Save
   scope.formSave = function() {
      Rest.setUrl(defaultUrl + $routeParams.id + '/groups/');
      var data = {}
      for (var fld in form.fields) {
          data[fld] = scope[fld];   
      } 
      Rest.post(data)
          .success( function(data, status, headers, config) {
              ReturnToCaller(1);
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to add new group. Post returned status: ' + status });
              });
      };

   // Cancel
   scope.formReset = function() {
      // Defaults
      generator.reset();
      }; 

}

GroupsAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'GroupForm', 'GenerateForm', 
                      'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'LookUpInventoryInit' ]; 


function GroupsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, GroupForm, 
                     GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, 
                     RelatedPaginateInit, ReturnToCaller, ClearScope, LookUpInventoryInit) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var defaultUrl='/api/v1/groups/';
   var generator = GenerateForm;
   var form = GroupForm;
   var scope = generator.inject(form, {mode: 'edit', related: true});
   generator.reset();
   var master = {};
   var id = $routeParams.id;
   var relatedSets = {};

   LookUpInventoryInit({ scope: scope });

   // After the Organization is loaded, retrieve each related set
   scope.$on('groupLoaded', function() {
       Rest.setUrl(scope['inventory_url']);
       Rest.get()
           .success( function(data, status, headers, config) {
               scope['inventory_name'] = data.name;
               master['inventory_name'] = data.name;
               })
           .error( function(data, status, headers, config) {
               ProcessErrors(scope, data, status, null,
                             { hdr: 'Error!', msg: 'Failed to retrieve: ' + scope.orgnization_url + '. GET status: ' + status });
               });
       for (var set in relatedSets) {
           scope.search(relatedSets[set].iterator);
       }
       });

   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl + ':id/'); 
   Rest.get({ params: {id: id} })
       .success( function(data, status, headers, config) {
           LoadBreadCrumbs();
           for (var fld in form.fields) {
              if (data[fld]) {
                 scope[fld] = data[fld];
                 master[fld] = scope[fld];
              }
           }
           var related = data.related;
           for (var set in form.related) {
               if (related[set]) {
                  relatedSets[set] = { url: related[set], iterator: form.related[set].iterator };
               }
           }
           // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
           RelatedSearchInit({ scope: scope, form: form, relatedSets: relatedSets });
           RelatedPaginateInit({ scope: scope, relatedSets: relatedSets });
           scope['inventory_url'] = data.related.inventory;
           scope.$emit('groupLoaded');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to retrieve group: ' + $routeParams.id + '. GET status: ' + status });
           });
   
   // Save changes to the parent
   scope.formSave = function() {
      Rest.setUrl(defaultUrl + id + '/');
      var data = {}
      for (var fld in form.fields) {
          data[fld] = scope[fld];   
      } 
      Rest.put(data)
          .success( function(data, status, headers, config) {
              var base = $location.path().replace(/^\//,'').split('/')[0];
              (base == 'inventories') ? ReturnToCaller() : ReturnToCaller(1);
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to update host: ' + $routeParams.id + '. PUT status: ' + status });
              });
      };

   // Cancel
   scope.formReset = function() {
      generator.reset();
      for (var fld in master) {
          scope[fld] = master[fld];
      }
      };

}

HostsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'HostForm', 
                      'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                      'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'LookUpInventoryInit' ]; 
  