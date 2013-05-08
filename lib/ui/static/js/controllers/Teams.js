/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Teams.js
 *  
 *  Controller functions for the Team model.
 *
 */

'use strict';

function TeamsList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, TeamList,
                    GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                    ClearScope, ProcessErrors, SetTeamListeners)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
    var list = TeamList;
    var defaultUrl = '/api/v1/teams/';
    var view = GenerateList;
    var paths = $location.path().replace(/^\//,'').split('/');
    var mode = (paths[0] == 'teams') ? 'edit' : 'select';      // if base path 'teams', we're here to add/edit teams
    var scope = view.inject(list, { mode: mode });    // Inject our view
    scope.selected = [];
  
    //SetTeamListeners({ scope: scope, set: 'teams', iterator: list.iterator });
    SearchInit({ scope: scope, set: 'teams', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();
    
    scope.addTeam = function() {
       $location.path($location.path() + '/add');
       }

    scope.editTeam = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteTeam = function(id, name) {
       
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
       Rest.setUrl('/api/v1/organization/' + organization_id + '/');
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
                    // there is no way to know which user raised the error. no data comes
                    // back from the api call. 
                    //   $('td.username-column').each(function(index) {
                    //      if ($(this).text() == scope.queue[i].username) {
                    //         $(this).addClass("error");
                    //      }
                    //   });
                 }
             }
             if (errors > 0) {
                Alert('Error', 'There was an error while adding one or more of the selected teams.');  
             }
             else {
                ReturnToCaller(1);
             }
          }
          });
       
       if (scope.selected.length > 0 ) {
          var team = null;
          for (var i=0; i < scope.selected.length; i++) {
              for (var j=0; j < scope.teams.length; j++) {
                  if (scope.teams[j].id == scope.selected[i]) {
                     team = scope.teams[j];
                  }
              }
              if (team !== null) {
                 Rest.post(team)
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

    scope.toggle_team = function(idx) {
       if (scope.selected.indexOf(idx) > -1) {
          scope.selected.splice(scope.selected.indexOf(idx),1);
       }
       else {
          scope.selected.push(idx);
       }
       }
}

TeamsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'TeamList', 'GenerateList', 
                      'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
                       'SetTeamListeners' ];


function TeamsAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, TeamForm, 
                         GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
                         GenerateList, OrganizationList, SearchInit, PaginateInit, TeamLookUpOrganizationInit) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var defaultUrl = '/api/v1/teams/';
   var form = TeamForm;
   var generator = GenerateForm;
   var scope = generator.inject(form, {mode: 'add', related: false});
   generator.reset();
   LoadBreadCrumbs();
   TeamLookUpOrganizationInit({ scope: scope });
   
   // Save
   scope.formSave = function() {
      Rest.setUrl(defaultUrl);
      var data = {}
      for (var fld in form.fields) {
          data[fld] = scope[fld];
      } 
      Rest.post(data)
          .success( function(data, status, headers, config) {
              ReturnToCaller();
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

TeamsAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'TeamForm', 'GenerateForm', 
                     'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope', 'GenerateList',
                     'OrganizationList', 'SearchInit', 'PaginateInit', 'TeamLookUpOrganizationInit' ]; 


function TeamsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, TeamForm, 
                    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, 
                    RelatedPaginateInit, ReturnToCaller, ClearScope, TeamLookUpOrganizationInit, Prompt) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var defaultUrl='/api/v1/teams/';
   var generator = GenerateForm;
   var form = TeamForm;
   var scope = generator.inject(form, {mode: 'edit', related: true});
   generator.reset();
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var master = {};
   var id = $routeParams.id;
   var relatedSets = {}; 
   
   TeamLookUpOrganizationInit({ scope: scope });

   // Retrieve each related set and any lookups
   scope.$on('teamLoaded', function() {
       Rest.setUrl(scope['organization_url']);
       Rest.get()
           .success( function(data, status, headers, config) {
               scope['organization_name'] = data.name;
               master['organization_name'] = data.name;
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
           LoadBreadCrumbs({ path: '/teams/' + id, title: data.name });
           console.log(data);
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
           scope['organization_url'] = data.related.organization;
           scope.$emit('teamLoaded');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to retrieve team: ' + $routeParams.id + '. GET status: ' + status });
           });

   // Save changes to the parent
   scope.formSave = function() {
      Rest.setUrl(defaultUrl + $routeParams.id);
      var data = {}
      for (var fld in form.fields) {
          data[fld] = scope[fld];   
      } 
      Rest.put(data)
          .success( function(data, status, headers, config) {
              var base = $location.path().replace(/^\//,'').split('/')[0];
              (base == 'teams') ? ReturnToCaller() : ReturnToCaller(1);
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                            { hdr: 'Error!', msg: 'Failed to update team: ' + $routeParams.id + '. PUT status: ' + status });
              });
      };

   // Cancel
   scope.formReset = function() {
      generator.reset();
      for (var fld in master) {
          scope[fld] = master[fld];
      }
      };

   // Related set: Add button
   scope.add = function(set) {
      $rootScope.flashMessage = null;
      $location.path('/' + base + '/' + $routeParams.id + '/' + set + '/add');
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
       
      }

}

TeamsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'TeamForm', 
                      'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                      'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'TeamLookUpOrganizationInit', 'Prompt'
                      ]; 
  