/************************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *
 *  Organizations.js
 *  
 *  Controller functions for Organization model.
 *
 */

'use strict';

function OrganizationsList ($routeParams, $scope, $rootScope, $location, $log, Rest, Alert, LoadBreadCrumbs, Prompt,
                            GenerateList, OrganizationList, SearchInit, PaginateInit, ClearScope, ProcessErrors,
                            GetBasePath, SelectionInit, Wait, Stream)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.

    var list = OrganizationList;
    var generate = GenerateList;
    var paths = $location.path().replace(/^\//,'').split('/');
    var mode = (paths[0] == 'organizations') ? 'edit' : 'select';      // if base path 'users', we're here to add/edit users
    var scope = generate.inject(OrganizationList, { mode: mode });         // Inject our view
    var defaultUrl = GetBasePath('organizations');
    var iterator = list.iterator;
    $rootScope.flashMessage = null;

    LoadBreadCrumbs();
    
    var url = GetBasePath('projects') + $routeParams.project_id + '/organizations/';
    SelectionInit({ scope: scope, list: list, url: url, returnToCaller: 1 });

    if (scope.removePostRefresh) {
       scope.removePostRefresh();
    }
    scope.removePostRefresh = scope.$on('PostRefresh', function() {
        // Cleanup after a delete
        Wait('stop');
        $('#prompt-modal').off();
        });
    
    // Initialize search and paginate pieces and load data
    SearchInit({ scope: scope, set: list.name, list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    scope.showActivity = function() { Stream({ scope: scope }); } 

    scope.addOrganization = function() {
       $location.path($location.path() + '/add');
       }

    scope.editOrganization = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteOrganization = function(id, name) {
       
       var action = function() {
           $('#prompt-modal').on('hidden.bs.modal', function(){ Wait('start'); });
           $('#prompt-modal').modal('hide');
           var url = defaultUrl + id + '/';
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
}

OrganizationsList.$inject=[ '$routeParams', '$scope', '$rootScope', '$location', '$log', 'Rest', 'Alert', 'LoadBreadCrumbs', 'Prompt',
                            'GenerateList', 'OrganizationList', 'SearchInit', 'PaginateInit', 'ClearScope', 'ProcessErrors',
                            'GetBasePath', 'SelectionInit', 'Wait', 'Stream'];


function OrganizationsAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, OrganizationForm, 
                           GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath,
                           ReturnToCaller, Wait) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var generator = GenerateForm;
   var form = OrganizationForm;
   var scope = generator.inject(form, {mode: 'add', related: false});
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var defaultUrl = GetBasePath('organizations');
   generator.reset();

   LoadBreadCrumbs();

   // Save
   scope.formSave = function() {
      generator.clearApiErrors();
      Wait('start');
      var url = GetBasePath(base);
      url += (base != 'organizations') ? $routeParams['project_id'] + '/organizations/' : '';
      Rest.setUrl(url);
      Rest.post({ name: $scope.name, 
                  description: $scope.description })
          .success( function(data, status, headers, config) {  
              Wait('stop');
              if (base == 'organizations') {
                 $rootScope.flashMessage = "New organization successfully created!";
                 $location.path('/organizations/' + data.id);
              }
              else {
                 ReturnToCaller(1);
              }
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                  { hdr: 'Error!', msg: 'Failed to add new organization. Post returned status: ' + status });
              });
      };

   // Cancel
   scope.formReset = function() {
      $rootScope.flashMessage = null;
      generator.reset();
      }; 
}

OrganizationsAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'OrganizationForm', 
                             'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath',
                             'ReturnToCaller', 'Wait'];


function OrganizationsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, OrganizationForm, 
                            GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit,
                            RelatedPaginateInit, Prompt, ClearScope, GetBasePath, Wait, Stream) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var form = OrganizationForm;
   var generator = GenerateForm;
   var scope = GenerateForm.inject(form, {mode: 'edit', related: true});
   generator.reset();
   
   var defaultUrl = GetBasePath('organizations');
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var master = {};
   var id = $routeParams.organization_id;
   var relatedSets = {}; 

   // After the Organization is loaded, retrieve each related set
   if (scope.organizationLoadedRemove) {
      scope.organizationLoadedRemove();
   }
   scope.organizationLoadedRemove = scope.$on('organizationLoaded', function() {
       for (var set in relatedSets) {
           scope.search(relatedSets[set].iterator);
       }
       Wait('stop');
       });

   // Retrieve detail record and prepopulate the form
   Wait('start');
   Rest.setUrl(defaultUrl + id + '/'); 
   Rest.get()
       .success( function(data, status, headers, config) {
           LoadBreadCrumbs({ path: '/organizations/' + id, title: data.name });
           for (var fld in form.fields) {
              if (data[fld]) {
                 scope[fld] = data[fld];
                 master[fld] = data[fld];
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
           scope.$emit('organizationLoaded');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
               { hdr: 'Error!', msg: 'Failed to retrieve organization: ' + $routeParams.id + '. GET status: ' + status });
           });
   
   
   // Save changes to the parent
   scope.formSave = function() {
      generator.clearApiErrors();
      Wait('start');
      var params = {};
      for (var fld in form.fields) {
          params[fld] = scope[fld];
      }
      Rest.setUrl(defaultUrl + id + '/');
      Rest.put(params)
          .success( function(data, status, headers, config) {
              Wait('stop');
              master = params;
              $rootScope.flashMessage = "Your changes were successfully saved!";
              })
          .error( function(data, status, headers, config) {
              Wait('stop');
              ProcessErrors(scope, data, status, OrganizationForm,
                  { hdr: 'Error!', msg: 'Failed to update organization: ' + id + '. PUT status: ' + status });
              });
      };

   scope.showActivity = function() { Stream({ scope: scope }); } 

   // Reset the form
   scope.formReset = function() {
      $rootScope.flashMessage = null;
      generator.reset();
      for (var fld in master) {
          scope[fld] = master[fld];
      }
      };

   // Related set: Add button
   scope.add = function(set) {
      $rootScope.flashMessage = null;
      $location.path('/' + base + '/' + $routeParams.organization_id + '/' + set);
      };

   // Related set: Edit button
   scope.edit = function(set, id, name) {
      $rootScope.flashMessage = null;
      $location.path('/' + set + '/' + id);
      };

   // Related set: Delete button
   scope['delete'] = function(set, itm_id, name, title) {
      $rootScope.flashMessage = null;
      
      var action = function() {
          Wait('start');
          var url = defaultUrl + $routeParams.organization_id + '/' + set + '/';
          Rest.setUrl(url);
          Rest.post({ id: itm_id, disassociate: 1 })
              .success( function(data, status, headers, config) {
                  Wait('stop');
                  $('#prompt-modal').modal('hide');
                  scope.search(form.related[set].iterator);
                  })
              .error( function(data, status, headers, config) {
                  Wait('stop');
                  $('#prompt-modal').modal('hide');
                  ProcessErrors(scope, data, status, null,
                            { hdr: 'Error!', msg: 'Call to ' + url + ' failed. POST returned status: ' + status });
                  });      
          };

       Prompt({ hdr: 'Delete', 
                body: 'Are you sure you want to remove ' + name + ' from ' + scope.name + ' ' + title + '?',
                action: action
                });
       
      }
}

OrganizationsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'OrganizationForm', 
                              'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit',
                              'RelatedPaginateInit', 'Prompt', 'ClearScope', 'GetBasePath', 'Wait', 'Stream'];
