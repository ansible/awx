/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  JobTemplates.js
 *  
 *  Controller functions for the Job Template model.
 *
 */

'use strict';

function JobTemplatesList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobTemplateList,
                           GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                           ClearScope, ProcessErrors, GetBasePath, PromptPasswords, JobTemplateForm, CredentialList,
                           LookUpInit)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
    var list = JobTemplateList;
    var defaultUrl = GetBasePath('job_templates');
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var mode = (base == 'job_templates') ? 'edit' : 'select'; 
    var scope = view.inject(list, { mode: mode });
    scope.selected = [];
  
    SearchInit({ scope: scope, set: 'job_templates', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();
    
    scope.addJobTemplate = function() {
       $location.path($location.path() + '/add');
       }

    scope.editJobTemplate = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteJobTemplate = function(id, name) {
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
       Rest.setUrl(defaultUrl);
       scope.queue = [];

       if (scope.callFinishedRemove) {
          scope.callFinishedRemove();
       }
       scope.callFinishedRemove = scope.$on('callFinished', function() {
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
                Alert('Error', 'There was an error while adding one or more of the selected templates.');  
             }
             else {
                ReturnToCaller(1);
             }
          }
          });

       if (scope.selected.length > 0 ) {
          var template = null;
          for (var i=0; i < scope.selected.length; i++) {
              for (var j=0; j < scope.job_templates.length; j++) {
                  if (scope.job_templates[j].id == scope.selected[i]) {
                     template = scope.job_templates[j];
                  }
              }
              if (template !== null) {
                 Rest.post(template)
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

    scope.toggle_job_template = function(id) {
      if (scope.selected.indexOf(id) > -1) {
          scope.selected.splice(scope.selected.indexOf(id),1);
       }
       else {
          scope.selected.push(id);
       }
       if (scope[list.iterator + "_" + id + "_class"] == "success") {
          scope[list.iterator + "_" + id + "_class"] = "";
          //$('input[name="check_' + id + '"]').checked = false;
          document.getElementById('check_' + id).checked = false;
       }
       else {
          scope[list.iterator + "_" + id + "_class"] = "success";
          //$('input[name="check_' + id + '"]').checked = true;
          document.getElementById('check_' + id).checked = true;
       }
       }

    function postJob(data) {
        // Create the job record
        (scope.credentialWatchRemove) ? scope.credentialWatchRemove() : null;
        var dt = new Date().toISOString();
        Rest.setUrl(data.related.jobs);
        Rest.post({
            name: data.name + ' ' + dt,        // job name required and unique
            description: data.description, 
            job_template: data.id, 
            inventory: data.inventory, 
            project: data.project, 
            playbook: data.playbook, 
            credential: data.credential, 
            forks: data.forks, 
            limit: data.limit, 
            verbosity: data.verbosity, 
            extra_vars: data.extra_vars
            })
            .success( function(data, status, headers, config) {
                if (data.passwords_needed_to_start.length > 0) {
                   // Passwords needed. Prompt for passwords, then start job.
                   PromptPasswords({
                       scope: scope,
                       passwords: data.passwords_needed_to_start,
                       start_url: data.related.start
                       });
                }
                else {
                   // No passwords needed, start the job!
                   Rest.setUrl(data.related.start); 
                   Rest.post()
                       .success( function(data, status, headers, config) {
                           $location.path('/jobs');
                           })
                       .error( function(data, status, headers, config) { 
                           ProcessErrors(scope, data, status, null,
                               { hdr: 'Error!', msg: 'Failed to start job. POST returned status: ' + status });
                           });
                }
                })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                   { hdr: 'Error!', msg: 'Failed to create job. POST returned status: ' + status });
                });
        };

    scope.submitJob = function(id) {
        // Get the job details
        Rest.setUrl(defaultUrl + id + '/');
        Rest.get()
            .success( function(data, status, headers, config) {
                // Create a job record
                if (data.credential == '' || data.credential == null) {
                   // Template does not have credential, prompt for one
                   if (scope.credentialWatchRemove) {
                      scope.credentialWatchRemove();
                   }
                   scope.credentialWatchRemove = scope.$watch('credential', function(newVal, oldVal) {
                       if (newVal !== oldVal) {
                          // After user selects a credential from the modal,
                          // submit the job
                          if (scope.credential != '' && scope.credential !== null && scope.credential !== undefined) {
                             data.credential = scope.credential;
                             postJob(data);
                          }
                       }
                       });
                   LookUpInit({
                       scope: scope,
                       form: JobTemplateForm,
                       current_item: null,
                       list: CredentialList, 
                       field: 'credential',
                       hdr: 'Credential Required'
                       });
                   scope.lookUpCredential();
                }
                else {
                   // We have what we need, submit the job
                   postJob(data);
                }
            })
            .error( function(data, status, headers, config) {
                ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get job template details. GET returned status: ' + status });
            });
        };

}

JobTemplatesList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobTemplateList',
                             'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
                             'ProcessErrors','GetBasePath', 'PromptPasswords', 'JobTemplateForm', 'CredentialList', 'LookUpInit'
                             ];

function JobTemplatesAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, JobTemplateForm, 
                          GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, ClearScope,
                          GetBasePath, InventoryList, CredentialList, ProjectList, LookUpInit) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var defaultUrl = GetBasePath('job_templates');
   var form = JobTemplateForm;
   var generator = GenerateForm;
   var scope = generator.inject(form, {mode: 'add', related: false});
   generator.reset();
   LoadBreadCrumbs();

   LookUpInit({
      scope: scope,
      form: form,
      current_item: null,
      list: InventoryList, 
      field: 'inventory' 
      });

   LookUpInit({
      scope: scope,
      form: form,
      current_item: null,
      list: CredentialList, 
      field: 'credential' 
      });

   // Update playbook select whenever project value changes
   var selectPlaybook = function(oldValue, newValue) {
       if (oldValue != newValue) {
          if (scope.project) {
             var url = GetBasePath('projects') + scope.project + '/playbooks/'; 
             Rest.setUrl(url);
             Rest.get()
                 .success( function(data, status, headers, config) {
                     var opts = [];
                     for (var i=0; i < data.length; i++) {
                         opts.push(data[i]);
                     }
                     scope.playbook_options = opts;
                     })
                .error( function(data, status, headers, config) {
                     ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to get playbook list for ' + url +'. GET returned status: ' + status });
                     });
          }
       }
       };
  
   // Register a watcher on project_name
   if (scope.selectPlaybookUnregister) {
      scope.selectPlaybookUnregister();
   }
   scope.selectPlaybookUnregister = scope.$watch('project_name', selectPlaybook);

   LookUpInit({
       scope: scope,
       form: form,
       current_item: null,
       list: ProjectList, 
       field: 'project'
       });

   scope.job_type_options = [{ value: 'run', label: 'Run' }, { value: 'check', label: 'Check' }];
   scope.playbook_options = [];         

   // Save
   scope.formSave = function() {
      Rest.setUrl(defaultUrl);
      var data = {}
      for (var fld in form.fields) {
          if (form.fields[fld].type == 'select' && fld != 'playbook') {
             data[fld] = scope[fld].value;
          }
          else {
             data[fld] = scope[fld];
          }      
      }
      Rest.post(data)
          .success( function(data, status, headers, config) {
              var base = $location.path().replace(/^\//,'').split('/')[0];
              (base == 'job_templates') ? ReturnToCaller() : ReturnToCaller(1);
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                  { hdr: 'Error!', msg: 'Failed to add new project. POST returned status: ' + status });
              });
      };

   // Reset
   scope.formReset = function() {
      // Defaults
      generator.reset();
      };

}

JobTemplatesAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobTemplateForm',
                            'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 'ClearScope',
                            'GetBasePath', 'InventoryList', 'CredentialList', 'ProjectList', 'LookUpInit' ]; 


function JobTemplatesEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, JobTemplateForm, 
                           GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit, 
                           RelatedPaginateInit, ReturnToCaller, ClearScope, InventoryList, CredentialList,
                           ProjectList, LookUpInit, PromptPasswords, GetBasePath) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var defaultUrl= GetBasePath('job_templates');
   var generator = GenerateForm;
   var form = JobTemplateForm;
   var scope = generator.inject(form, {mode: 'edit', related: true});
   generator.reset();
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var master = {};
   var id = $routeParams.id;
   var relatedSets = {}; 


   function getPlaybooks(project) {
       if (project !== null && project !== '' && project !== undefined) {
           var url = GetBasePath('projects') + project + '/playbooks/';
           Rest.setUrl(url);
           Rest.get()
               .success( function(data, status, headers, config) {                      
                   scope.playbook_options = [];
                   for (var i=0; i < data.length; i++) {
                       scope.playbook_options.push(data[i]);
                   }
                   })
               .error( function(data, status, headers, config) {
                   ProcessErrors(scope, data, status, form,
                       { hdr: 'Error!', msg: 'Failed to get playbook list for ' + url +'. GET returned status: ' + status });
                   });
       }
       }

   // Register a watcher on project_name. Refresh the playbook list on change.
   if (scope.selectPlaybookUnregister) {
      scope.selectPlaybookUnregister();
   }
   scope.selectPlaybookUnregister = scope.$watch('project_name', function(oldValue, newValue) {
       if (oldValue !== newValue && newValue !== '' && newValue !== null && newValue !== undefined) {
          scope.playbook = null;
          getPlaybooks(scope.project);
       }
       });
   
   // Retrieve each related set and populate the playbook list
   if (scope.jobTemplateLoadedRemove) {
      scope.jobTemplateLoadedRemove();
   }
   scope.jobTemplateLoadedRemove = scope.$on('jobTemplateLoaded', function() {
       for (var set in relatedSets) {
           scope.search(relatedSets[set].iterator);
       }
       getPlaybooks(scope.project);
       });

   // Our job type options
   scope.job_type_options = [{ value: 'run', label: 'Run' }, { value: 'check', label: 'Check' }];
   scope.playbook_options = null;
   scope.playbook = null; 

   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl + ':id/'); 
   Rest.get({ params: {id: id} })
       .success( function(data, status, headers, config) {
           LoadBreadCrumbs({ path: '/job_templates/' + id, title: data.name });
           for (var fld in form.fields) {
              if (data[fld] !== null && data[fld] !== undefined) {  
                 if (form.fields[fld].type == 'select') {
                    if (scope[fld + '_options'] && scope[fld + '_options'].length > 0) {
                       for (var i=0; i < scope[fld + '_options'].length; i++) {
                           if (data[fld] == scope[fld + '_options'][i].value) {
                              scope[fld] = scope[fld + '_options'][i];
                           }
                       }
                    }
                    else {
                       scope[fld] = data[fld];
                    }
                 }
                 else {
                    scope[fld] = data[fld];
                 }
                 master[fld] = scope[fld];
              }
              if (form.fields[fld].type == 'lookup' && data.summary_fields[form.fields[fld].sourceModel]) {
                  scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] = 
                      data.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
                  master[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] =
                      scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField];
              }
           }
           scope.url = data.url; 
           var related = data.related;
           for (var set in form.related) {
               if (related[set]) {
                  relatedSets[set] = { url: related[set], iterator: form.related[set].iterator };
               }
           }

           LookUpInit({
               scope: scope,
               form: form,
               current_item: data.inventory,
               list: InventoryList, 
               field: 'inventory' 
               });

           LookUpInit({
               scope: scope,
               form: form,
               current_item: data.credential,
               list: CredentialList, 
               field: 'credential' 
               });

           LookUpInit({
               scope: scope,
               form: form,
               current_item: data.project,
               list: ProjectList, 
               field: 'project'
               });

           // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
           RelatedSearchInit({ scope: scope, form: form, relatedSets: relatedSets });
           RelatedPaginateInit({ scope: scope, relatedSets: relatedSets });
           scope.$emit('jobTemplateLoaded');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to retrieve job template: ' + $routeParams.id + '. GET status: ' + status });
           });

   // Save changes to the parent
   scope.formSave = function() {
      Rest.setUrl(defaultUrl + $routeParams.id + '/');
      var data = {}
      for (var fld in form.fields) {
          if (form.fields[fld].type == 'select' && fld != 'playbook') {
             data[fld] = scope[fld].value;
          }
          else {
             data[fld] = scope[fld];
          }   
      } 
      Rest.put(data)
          .success( function(data, status, headers, config) {
              var base = $location.path().replace(/^\//,'').split('/')[0];
              (base == 'job_templates') ? ReturnToCaller() : ReturnToCaller(1);
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
      $location.path('/' + base + '/' + $routeParams.id + '/' + set);
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

JobTemplatesEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobTemplateForm', 
                             'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                             'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'InventoryList', 'CredentialList',
                             'ProjectList', 'LookUpInit', 'PromptPasswords', 'GetBasePath'
                             ]; 
