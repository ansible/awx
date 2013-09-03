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
                       ClearScope, ProcessErrors, GetBasePath, SelectionInit, SCMUpdate)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
    var list = ProjectList;
    var defaultUrl = GetBasePath('projects');
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var mode = (base == 'projects') ? 'edit' : 'select';
    var scope = view.inject(list, { mode: mode });
    $rootScope.flashMessage = null;
    
    var url = (base == 'teams') ? GetBasePath('teams') + $routeParams.team_id + '/projects/' : defaultUrl;
    SelectionInit({ scope: scope, list: list, url: url, returnToCaller: 1 });
    
    if (scope.projectsPostRefresh) {
       scope.projectsPostRefresh();
    }
    scope.projectsPostRefresh = scope.$on('PostRefresh', function() {
        for (var i=0; i < scope.projects.length; i++) {
            if (scope.projects[i].scm_type == null) {
               // override the last_update_failed on manual projects- it should be false so we get a 
               // green badge.  if projet scm_type changed from something to manual, last_update_failed
               // will contain status of last update, which is not what we want.
               scope.projects[i].last_update_failed = false;  
            }
        }
        });

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
           Rest.destroy()
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

    scope.SCMUpdate = function(project_id) {
       for (var i=0; i < scope.projects.length; i++) {
           if (scope.projects[i].id == project_id) {
              if (scope.projects[i].scm_type == "") {
                 Alert('Missing SCM Setup', 'Before running an SCM update, edit the project and provide the SCM access information.', 'alert-info');
              }
              else {
                 SCMUpdate({ scope: scope, project_id: project_id });
              }
              break;
           }
       }
       }
}

ProjectsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'ProjectList', 'GenerateList', 
                         'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope', 'ProcessErrors',
                         'GetBasePath', 'SelectionInit', 'SCMUpdate'];


function ProjectsAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, ProjectsForm, 
                      GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, 
                      GetBasePath, ReturnToCaller, GetProjectPath, LookUpInit, OrganizationList) 
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
   var master = {};

   generator.reset();
   LoadBreadCrumbs();
   GetProjectPath({ scope: scope, master: master });
   //console.log(scope.)
   
   scope.scm_type = null;
   master.scm_type = null;
   scope.scm_type_options = [
       { label: 'Git', value: 'git' },
       { label: 'SVN', value: 'svn' },
       { label: 'Mercurial', value: 'hg'}];

   LookUpInit({
       scope: scope,
       form: form,
       current_item: null,
       list: OrganizationList, 
       field: 'organization' 
       });

   // Save
   scope.formSave = function() {
       var data = {};
       for (var fld in form.fields) {
           if (form.fields[fld].type == 'checkbox_group') {
              for (var i=0; i < form.fields[fld].fields.length; i++) {
                  data[form.fields[fld].fields[i].name] = scope[form.fields[fld].fields[i].name];
              }
           }
           else {
              data[fld] = scope[fld];
           }
        }
       if (scope.scm_type) {
          data.scm_type = scope.scm_type.value;
          delete data.local_path;
       }
       var url = (base == 'teams') ? GetBasePath('teams') + $routeParams.team_id + '/projects/' : defaultUrl;
       Rest.setUrl(url);
       Rest.post(data)
           .success( function(data, status, headers, config) {
               var id = data.id;
               var url = GetBasePath('projects') + id + '/organizations/';
               var org = { id: scope.organization };
               Rest.setUrl(url);
               Rest.post(org)
                   .success( function(data, status, headers, config) {
                       $rootScope.flashMessage = "New project successfully created!";
                       (base == 'projects') ? ReturnToCaller() : ReturnToCaller(1);
                       })
                   .error( function(data, status, headers, config) {
                       ProcessErrors(scope, data, status, ProjectsForm,
                           { hdr: 'Error!', msg: 'Failed to add organization to project. POST returned status: ' + status });
                       });
               })
          .error( function(data, status, headers, config) {
               ProcessErrors(scope, data, status, ProjectsForm,
                   { hdr: 'Error!', msg: 'Failed to create new project. POST returned status: ' + status });
               });
       };

   scope.scmChange = function() {
       // When an scm_type is set, path is not required
       scope.pathRequired = (scope.scm_type) ? false : true;
       scope.scmBranchLabel = (scope.scm_type.value == 'svn') ? 'Revision #' : 'SCM Branch'; 
       }

   // Cancel
   scope.formReset = function() {
       $rootScope.flashMessage = null;
       generator.reset();
       for (var fld in master) {
           scope[fld] = master[fld];
       }
       }; 
}

ProjectsAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'ProjectsForm', 
                        'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath',
                        'ReturnToCaller', 'GetProjectPath', 'LookUpInit', 'OrganizationList'
                        ];


function ProjectsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, ProjectsForm, 
                       GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit,
                       RelatedPaginateInit, Prompt, ClearScope, GetBasePath, ReturnToCaller, GetProjectPath,
                       Authorization) 
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

   scope.scm_type_options = [
       { label: 'Git', value: 'git' },
       { label: 'SVN', value: 'svn' },
       { label: 'Mercurial', value: 'hg'}];
   
   scope.project_local_paths = [];
   scope.base_dir = ''; 

   function setAskCheckboxes() {
       for (var fld in form.fields) {
           if (form.fields[fld].type == 'password' && form.fields[fld].ask && scope[fld] == 'ASK') {
              // turn on 'ask' checkbox for password fields with value of 'ASK'
              $("#" + fld + "-clear-btn").attr("disabled","disabled");
              scope[fld + '_ask'] = true;
           }
           else {
              scope[fld + '_ask'] = false;
              $("#" + fld + "-clear-btn").removeAttr("disabled");
           }
       }
       } 

   // After the project is loaded, retrieve each related set
   if (scope.projectLoadedRemove) {
      scope.projectLoadedRemove();
   }
   scope.projectLoadedRemove = scope.$on('projectLoaded', function() {
       for (var set in relatedSets) {
           scope.search(relatedSets[set].iterator);
       }
       if (Authorization.getUserInfo('is_superuser') == true) {
          GetProjectPath({ scope: scope, master: master });
       }
       else {
          var opts = [];
          opts.push(scope['local_path']);
          scope.project_local_paths = opts;
          scope.base_dir = 'You do not have access to view this property';
       }
       });

   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl); 
   Rest.get({ params: {id: id} })
       .success( function(data, status, headers, config) {
           LoadBreadCrumbs({ path: '/projects/' + id, title: data.name });
           for (var fld in form.fields) {
              if (form.fields[fld].type == 'checkbox_group') {
                 for (var i=0; i < form.fields[fld].fields.length; i++) {
                     scope[form.fields[fld].fields[i].name] = data[form.fields[fld].fields[i].name];
                     master[form.fields[fld].fields[i].name] = data[form.fields[fld].fields[i].name];
                 }
              }
              else {
                 if (data[fld]) {
                    scope[fld] = data[fld];
                    master[fld] = data[fld];
                 }
              }
           }
           var related = data.related;
           for (var set in form.related) {
               if (related[set]) {
                  relatedSets[set] = { url: related[set], iterator: form.related[set].iterator };
               }
           }

           if (data.scm_type !== "") {
              for (var i=0; i < scope.scm_type_options.length; i++) {
                  if (scope.scm_type_options[i].value == data.scm_type) {
                     scope.scm_type = scope.scm_type_options[i];
                     break;
                  }
              }
              scope.pathRequired = false;
           }
           else {
              scope.pathRequired = true;
           }

           master['scm_type'] = scope['scm_type'];
           setAskCheckboxes();
           
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
       $rootScope.flashMessage = null;
       var params = {};
       for (var fld in form.fields) {
           if (form.fields[fld].type == 'checkbox_group') {
              for (var i=0; i < form.fields[fld].fields.length; i++) {
                  params[form.fields[fld].fields[i].name] = scope[form.fields[fld].fields[i].name];
              }
           }
           else {
              params[fld] = scope[fld];
           }
       }
       if (scope.scm_type) {
          params.scm_type = scope.scm_type.value;
          delete params.local_path;
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
       $rootScope.flashMessage = null;
       generator.reset();
       for (var fld in master) {
           scope[fld] = master[fld];
       }
       };

   // Related set: Add button
   scope.add = function(set) {
       $rootScope.flashMessage = null;
       $location.path('/' + base + '/' + $routeParams.id + '/' + set);
       };

   // Related set: Edit button
   scope.edit = function(set, id, name) {
       $rootScope.flashMessage = null;
       $location.path('/' + set + '/' + id);
       };

   // Related set: Delete button
   scope['delete'] = function(set, itm_id, name, title) {
       var action = function() {
       var url = GetBasePath('projects') + id + '/' + set + '/';
       $rootScope.flashMessage = null;
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

   // Password change
   scope.clearPWConfirm = function(fld) {
       // If password value changes, make sure password_confirm must be re-entered
       scope[fld] = '';
       scope[form.name + '_form'][fld].$setValidity('awpassmatch', false);
       }
    
   // Respond to 'Ask at runtime?' checkbox
   scope.ask = function(fld, associated) {
       if (scope[fld + '_ask']) {
          $("#" + fld + "-clear-btn").attr("disabled","disabled");
          scope[fld] = 'ASK';
          scope[associated] = '';
          scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
       }
       else {
          $("#" + fld + "-clear-btn").removeAttr("disabled");
          scope[fld] = '';
          scope[associated] = '';
          scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
       }
       }

   scope.clear = function(fld, associated) {
       scope[fld] = '';
       scope[associated] = '';
       scope[form.name + '_form'][associated].$setValidity('awpassmatch', true);
       }

   scope.scmChange = function() {
       // When an scm_type is set, path is not required
       scope.pathRequired = (scope.scm_type) ? false : true;
       }
}

ProjectsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'ProjectsForm', 
                         'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit',
                         'RelatedPaginateInit', 'Prompt', 'ClearScope', 'GetBasePath', 'ReturnToCaller', 
                         'GetProjectPath', 'Authorization'
                          ];
