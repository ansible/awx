/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Projects.js
 *  
 *  Controller functions for the Projects model.
 *
 */

'use strict';

function ProjectsList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, ProjectList,
                       GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                       ClearScope, ProcessErrors, GetBasePath)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
    var list = ProjectList;
    var defaultUrl = GetBasePath('projects');
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var mode = (base == 'projects') ? 'edit' : 'select';
    var scope = view.inject(list, { mode: mode });
    scope.selected = [];
  
    SearchInit({ scope: scope, set: 'projects', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();
    
    scope.addProject = function() {
       $location.path($location.path() + '/add');
       }

    scope.editProject = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteProject = function(id, name) {
       
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
    
    scope.finishSelection = function() {
       var url = (base == 'teams') ? GetBasePath('teams') + $routeParams.team_id + '/projects/' : defaultUrl;
       Rest.setUrl(url);
       scope.queue = [];
     
       if (scope.callFinishedRemove) {
          scope.callFinishedRemove();
       }
       scope.callFinishedRemoved = scope.$on('callFinished', function() {
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
                 }
             }
             if (errors > 0) {
                Alert('Error', 'There was an error while adding one or more of the selected Pojects.');  
             }
             else {
                ReturnToCaller(1);
             }
          }
          });

       if (scope.selected.length > 0 ) {
          var project = null;
          for (var i=0; i < scope.selected.length; i++) {
              for (var j=0; j < scope.projects.length; j++) {
                  if (scope.projects[j].id == scope.selected[i]) {
                     project = scope.projects[j];
                  }
              }
              if (project !== null) {
                 Rest.post(project)
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
          ReturnToCaller(1);
       }  
    }

    scope.toggle_project = function(id) {
       if (scope[list.iterator + "_" + id + "_class"] == "success") {
          scope[list.iterator + "_" + id + "_class"] = "";
          document.getElementById('check_' + id).checked = false;
          if (scope.selected.indexOf(id) > -1) {
             scope.selected.splice(scope.selected.indexOf(id),1);
          }
       }
       else {
          scope[list.iterator + "_" + id + "_class"] = "success";
          document.getElementById('check_' + id).checked = true;
          if (scope.selected.indexOf(id) == -1) {
             scope.selected.push(id);
          }
       }
       }
}

ProjectsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'ProjectList', 'GenerateList', 
                         'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
                         'GetBasePath' ];


function ProjectsAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, ProjectsForm, 
                      GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, 
                      GetBasePath, ReturnToCaller) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var form = ProjectsForm;
   var generator = GenerateForm;
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var defaultUrl = GetBasePath('projects');
   var scope = generator.inject(form, {mode: 'add', related: false});
   var id = $routeParams.id;
   generator.reset();
   
   LoadBreadCrumbs();

   // Save
   scope.formSave = function() {
      var data = {};
      for (var fld in form.fields) {
          data[fld] = scope[fld];
      }
      var url = (base == 'teams') ? GetBasePath('teams') + $routeParams.team_id + '/projects/' : defaultUrl;
      Rest.setUrl(url);
      Rest.post(data)
          .success( function(data, status, headers, config) {
              (base == 'projects') ? ReturnToCaller() : ReturnToCaller(1);
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, ProjectsForm,
                            { hdr: 'Error!', msg: 'Failed to create new project. Post returned status: ' + status });
              });
      };

   // Cancel
   scope.formReset = function() {
      $rootScope.flashMessage = null;
      form.reset();
      }; 
}

ProjectsAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'ProjectsForm', 
                        'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath',
                        'ReturnToCaller'
                        ];


function ProjectsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, ProjectsForm, 
                       GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit,
                       RelatedPaginateInit, Prompt, ClearScope, GetBasePath, ReturnToCaller) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var form = ProjectsForm;
   var generator = GenerateForm;
   var scope = generator.inject(form, {mode: 'edit', related: true});
   generator.reset();
   
   var defaultUrl = GetBasePath('projects') + $routeParams.id + '/';
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var master = {};
   var id = $routeParams.id;
   var relatedSets = {}; 

   // After the project is loaded, retrieve each related set
   if (scope.projectLoadedRemove) {
      scope.projectLoadedRemove();
   }
   scope.projectLoadedRemove = scope.$on('projectLoaded', function() {
       for (var set in relatedSets) {
           scope.search(relatedSets[set].iterator);
       }
       });

   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl); 
   Rest.get({ params: {id: id} })
       .success( function(data, status, headers, config) {
           LoadBreadCrumbs({ path: '/projects/' + id, title: data.name });
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
           scope.$emit('projectLoaded');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to retrieve project: ' + id + '. GET status: ' + status });
           });
   
   
   // Save changes to the parent
   scope.formSave = function() {
      var params = {};
      for (var fld in form.fields) {
          params[fld] = scope[fld];
      }
      Rest.setUrl(defaultUrl);
      Rest.put(params)
          .success( function(data, status, headers, config) {
              ReturnToCaller();
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                { hdr: 'Error!', msg: 'Failed to update project: ' + id + '. PUT status: ' + status });
              });
      };

   // Reset the form
   scope.formReset = function() {
      form.reset();
      for (var fld in master) {
          scope[fld] = master[fld];
      }
      };

   // Related set: Add button
   scope.add = function(set) {
      $location.path('/' + base + '/' + $routeParams.id + '/' + set);
      };

   // Related set: Edit button
   scope.edit = function(set, id, name) {
      $location.path('/' + base + '/' + $routeParams.id + '/' + set + '/' + id);
      };

   // Related set: Delete button
   scope.delete = function(set, itm_id, name, title) {
      var action = function() {
          var url = GetBasePath('projects') + id + '/' + set + '/';
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

ProjectsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'ProjectsForm', 
                         'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit',
                         'RelatedPaginateInit', 'Prompt', 'ClearScope', 'GetBasePath', 'ReturnToCaller'
                          ];
