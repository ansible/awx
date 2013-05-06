/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Hosts.js
 *  
 *  Controller functions for Host model.
 *
 */

'use strict';

function HostsList ($scope, $rootScope, $location, $log, $routeParams, Rest, 
                    Alert, HostList, GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit,
                    ReturnToCaller, ClearScope)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.

    var list = HostList;
    var defaultUrl = '/api/v1/inventories/' + $routeParams.id + '/hosts/';
    var view = GenerateList;
    var paths = $location.path().replace(/^\//,'').split('/');
    var scope = view.inject(HostList, { mode: 'edit' });               // Inject our view
    scope.selected = [];
  
    SearchInit({ scope: scope, set: 'hosts', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);


    LoadBreadCrumbs();
    
    scope.addHost = function() {
       $location.path($location.path() + '/add');
       }

    scope.editHost = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteHost = function(id, name) {
       
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
                body: 'Are you sure you want to delete host ' + name + '?',
                action: action
                });
       }

}

HostsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'HostList', 'GenerateList', 
                      'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope' ];


function HostsAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, HostForm, 
                   GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var defaultUrl = '/api/v1/inventories/';
   var form = HostForm;
   var generator = GenerateForm;
   var scope = generator.inject(form, {mode: 'add', related: false});
   generator.reset();

   LoadBreadCrumbs();

   // Save
   scope.formSave = function() {
      Rest.setUrl(defaultUrl + $routeParams.id + '/hosts/');
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
                            { hdr: 'Error!', msg: 'Failed to add new host. Post returned status: ' + status });
              });
      };

   // Cancel
   scope.formReset = function() {
      // Defaults
      generator.reset();
      }; 

}

HostsAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'HostForm', 'GenerateForm', 
                     'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope' ]; 


function HostsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, UserForm, 
                    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, 
                    RelatedPaginateInit, ReturnToCaller, ClearScope, LookUpInventoryInit) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var defaultUrl='/api/v1/hosts/';
   var generator = GenerateForm;
   var form = UserForm;
   var scope = generator.inject(form, {mode: 'edit', related: true});
   generator.reset();
   var master = {};
   var id = $routeParams.id;
   var relatedSets = {};

   LookUpInventoryInit({ scope: scope });

   // After the Organization is loaded, retrieve each related set
   scope.$on('dataLoaded', function() {
       
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
           scope.$emit('dataLoaded');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to retrieve host: ' + $routeParams.id + '. GET status: ' + status });
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
  