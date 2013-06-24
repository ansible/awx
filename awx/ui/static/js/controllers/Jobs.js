/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Jobs.js
 *  
 *  Controller functions for the Job model.
 *
 */

'use strict';

function JobsListCtrl ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobList,
                       GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                       ClearScope, ProcessErrors, GetBasePath, LookUpInit, SubmitJob)
{
    ClearScope('htmlTemplate');
    var list = JobList;
    var defaultUrl = GetBasePath('jobs');
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var scope = view.inject(list, { mode: 'edit' });
    $rootScope.flashMessage = null;
    scope.selected = [];
  
    if (scope.PostRefreshRemove) {
       scope.PostRefreshRemove();
    }
    scope.PostRefreshRemove = scope.$on('PostRefresh', function() {
        $("tr.success").each(function(index) {
            // Make sure no rows have a green background
            var ngc = $(this).attr('ng-class');
            scope[ngc] = "";
            });
        });
    
    SearchInit({ scope: scope, set: 'jobs', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });

    // Called from Inventories page, failed jobs link. Find jobs for selected inventory.
    if ($routeParams['inventory__int']) {
       scope[list.iterator + 'SearchField'] = 'inventory'; 
       scope[list.iterator + 'SearchValue'] = $routeParams['inventory__int'];
       scope[list.iterator + 'SearchFieldLabel'] = 'Inventory';
    }
    scope.search(list.iterator);

    // Called from Inventories page, failed jobs link. Now sort by status so faild jobs appear at top of list
    if ($routeParams.order_by) {
       scope.sort($routeParams.order_by);
    }

    LoadBreadCrumbs();

    scope.refreshJob = function() {
       scope.search(list.iterator);
       }

    scope.editJob = function(id, name) {
       LoadBreadCrumbs({ path: '/jobs/' + id, title: name });
       $location.path($location.path() + '/' + id);
       }

    scope.viewEvents = function(id, name) {
       LoadBreadCrumbs({ path: '/jobs/' + id, title: name });
       $location.path($location.path() + '/' + id + '/job_events');
       }

    scope.viewSummary = function(id, name) {
       LoadBreadCrumbs({ path: '/jobs/' + id, title: name });
       $location.path($location.path() + '/' + id + '/job_host_summaries');
       }

    scope.deleteJob = function(id, name) {
       Rest.setUrl(defaultUrl + id + '/');
       Rest.get()
           .success( function(data, status, headers, config) { 
               var url, action_label, restcall, hdr; 
               if (data.status == 'pending' || data.status == 'running') {
                  url = data.related.cancel;
                  action_label = 'cancel';
                  hdr = 'Cancel Job';
               }
               else {
                  url = defaultUrl + id + '/';
                  action_label = 'delete';
                  hdr = 'Delete Job';
               }

               var action = function() {
                   Rest.setUrl(url);
                   if (action_label == 'cancel') {
                      Rest.post()
                          .success( function(data, status, headers, config) {
                              $('#prompt-modal').modal('hide');
                              scope.search(list.iterator);
                              })
                          .error( function(data, status, headers, config) {
                              $('#prompt-modal').modal('hide');
                              ProcessErrors(scope, data, status, null,
                                  { hdr: 'Error!', msg: 'Call to ' + url + ' failed. POST returned status: ' + status });
                              });
                   }
                   else {
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
                   } 
                   };

               Prompt({
                   hdr: hdr, 
                   body: 'Are you sure you want to ' + action_label + ' job ' + id + '?',
                   action: action
                   });
           })
           .error( function(data, status, headers, config) {
               ProcessErrors(scope, data, status, null,
                   { hdr: 'Error!', msg: 'Failed to get job details. GET returned status: ' + status });
           });
            
        }
  
    scope.submitJob = function(id, template) {
        SubmitJob({ scope: scope, id: id, template: template });
        }
}

JobsListCtrl.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobList',
                         'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
                         'ProcessErrors','GetBasePath', 'LookUpInit', 'SubmitJob'
                         ];


function JobsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, JobForm, 
                  GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit,
                  RelatedPaginateInit, ReturnToCaller, ClearScope, InventoryList, CredentialList,
                  ProjectList, LookUpInit, PromptPasswords, GetBasePath, md5Setup) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var defaultUrl= GetBasePath('jobs');
   var generator = GenerateForm;
   var form = JobForm;

   var scope = generator.inject(form, {mode: 'edit', related: true});
   generator.reset();
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var master = {};
   var id = $routeParams.id;
   var relatedSets = {};

   scope.statusSearchSpin = false;

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
   if (scope.jobLoadedRemove) {
      scope.jobLoadedRemove();
   }
   scope.jobLoadedRemove = scope.$on('jobLoaded', function() {
       
       scope[form.name + 'ReadOnly'] = (scope.status == 'new') ? false : true;
       
       // Load related sets
       for (var set in relatedSets) {
           scope.search(relatedSets[set].iterator);
       }
       // Set the playbook lookup
       getPlaybooks(scope.project);

       $('#forks-slider').slider("option", "value", scope.forks);
       $('#forks-slider').slider("disable");
      
       // Get job template and display/hide host callback fields
       Rest.setUrl(scope.template_url);
       Rest.get()
           .success( function(data, status, headers, config) {
               var dft = (data['host_config_key']) ? 'true' : 'false';
               scope['host_config_key'] = data['host_config_key'];
               md5Setup({
                   scope: scope, 
                   master: master, 
                   check_field: 'allow_callbacks',
                   default_val: dft
                   });
               $('input[type="checkbox"]').attr('disabled','disabled');
               $('#host_config_key-gen-btn').attr('disabled','disabled');
               })
           .error( function(data, status, headers, config) {
               ProcessErrors(scope, data, status, form,
                   { hdr: 'Error!', msg: 'Failed to retrieve job: ' + $routeParams.id + '. GET status: ' + status });
               });
       
       });

   // Our job type options
   scope.job_type_options = [{ value: 'run', label: 'Run' }, { value: 'check', label: 'Check' }];
   scope.verbosity_options = [
       { value: '0', label: 'Default' },
       { value: '1', label: 'Verbose' },
       { value: '3', label: 'Debug' }];
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
           
           for (var fld in form.statusFields) {
               if (data[fld] !== null && data[fld] !== undefined) {
                  scope[fld] = data[fld];
               }
           }
            
           $('input[type="text"], textarea').attr('readonly','readonly');
           $('select').prop('disabled', 'disabled');
           $('.lookup-btn').prop('disabled', 'disabled');

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
           scope.template_url = data.related.job_template;
           scope.$emit('jobLoaded');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
               { hdr: 'Error!', msg: 'Failed to retrieve job: ' + $routeParams.id + '. GET status: ' + status });
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
                            { hdr: 'Error!', msg: 'Failed to update job ' + $routeParams.id + '. PUT returned status: ' + status });
              });
      };

   // Cancel
   scope.formReset = function() {
      generator.reset();
      for (var fld in master) {
          scope[fld] = master[fld];
      }
      $('#forks-slider').slider("option", "value", scope.forks);
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
   scope['delete'] = function(set, itm_id, name, title) {
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

   scope.refresh = function() {
      scope.statusSearchSpin = true;
      Rest.setUrl(defaultUrl + id + '/'); 
      Rest.get()
          .success( function(data, status, headers, config) {
              scope.status = data.status; 
              scope.result_stdout = data.result_stdout;
              scope.result_traceback = data.result_traceback;
              scope.statusSearchSpin = false;
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, null,
                 { hdr: 'Error!', msg: 'Attempt to load job failed. GET returned status: ' + status });
              });
      }

  scope.jobSummary = function() {
      $location.path('/jobs/' + id + '/job_host_summaries');
      }

  scope.jobEvents = function() {
      $location.path('/jobs/' + id + '/job_events');
      }
}

JobsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobForm', 
                     'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                     'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'InventoryList', 'CredentialList',
                     'ProjectList', 'LookUpInit', 'PromptPasswords', 'GetBasePath', 'md5Setup'
                     ];
