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
                       ClearScope, ProcessErrors, GetBasePath, LookUpInit)
{
    ClearScope('htmlTemplate');
    var list = JobList;
    var defaultUrl = GetBasePath('jobs');
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var scope = view.inject(list, { mode: 'edit' });
    scope.selected = [];
  
    SearchInit({ scope: scope, set: 'jobs', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();

    scope.refreshJob = function() {
       scope.search(list.iterator);
       }

    scope.editJob = function(id) {
       $location.path($location.path() + '/' + id);
       }

    scope.viewEvents = function(id) {
       $location.path($location.path() + '/' + id + '/job_events');
       }

    scope.deleteJob = function(id, name) {
       Rest.setUrl(defaultUrl + id + '/');
       Rest.get()
           .success( function(data, status, headers, config) {
               
               var url, action_label, restcall, hdr; 

               if (data.status == 'pending') {
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
                   } 
                   };

               Prompt({ hdr: hdr, 
                        body: 'Are you sure you want to ' + action_label + ' job ' + id + '?',
                        action: action
                        });
           })
           .error( function(data, status, headers, config) {
               ProcessErrors(scope, data, status, null,
                   { hdr: 'Error!', msg: 'Failed to get job details. GET returned status: ' + status });
           });
            
        }
  
}

JobsListCtrl.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobList',
                         'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
                         'ProcessErrors','GetBasePath', 'LookUpInit'
                         ];


function JobsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, JobForm, 
                  GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, RelatedSearchInit,
                  RelatedPaginateInit, ReturnToCaller, ClearScope, InventoryList, CredentialList,
                  ProjectList, LookUpInit, PromptPasswords, GetBasePath) 
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
           
           for (var fld in form.statusFields) {
               if (data[fld] !== null && data[fld] !== undefined) {
                  scope[fld] = data[fld];
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
           scope.$emit('jobLoaded');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to retrieve job template: ' + $routeParams.id + '. GET status: ' + status });
           });

   // Save changes to the parent
   scope.formSave = function() {
      Rest.setUrl(defaultUrl + $routeParams.id);
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

JobsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobForm', 
                     'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'RelatedSearchInit', 
                     'RelatedPaginateInit', 'ReturnToCaller', 'ClearScope', 'InventoryList', 'CredentialList',
                     'ProjectList', 'LookUpInit', 'PromptPasswords', 'GetBasePath'
                     ];


function JobEvents ($scope, $rootScope, $compile, $location, $log, $routeParams, JobEventForm, 
                    GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, SearchInit, 
                    PaginateInit, GetBasePath) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var form = JobEventForm;
   var generator = GenerateForm;
   var scope = GenerateForm.inject(form, {mode: 'edit', related: true});
   generator.reset();
   
   var defaultUrl = GetBasePath('jobs') + $routeParams.id + '/job_events/';
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var master = {};
   var id = $routeParams.id;
   var relatedSets = {}; 

   if (scope.PostRefreshRemove){
      scope.PostRefreshRemove();
   }
   scope.PostRefreshRemove = scope.$on('PostRefresh', function() {
       var results = scope[form.items.event.set][0];
       // Disable Next/Prev buttons when we rich the end/beginning of array
       scope[form.items.event.iterator + 'NextUrlDisable'] = (scope[form.items.event.iterator + 'NextUrl']) ? "" : "disabled";
       scope[form.items.event.iterator + 'PrevUrlDisable'] = (scope[form.items.event.iterator + 'PrevUrl']) ? "" : "disabled";
       
       // Set the scope input field values
       for (var fld in form.items.event.fields) {
           if (fld == 'event_data') {
              scope.event_data = JSON.stringify(results[fld]);
           }
           else {
              if (results[fld]) {
                 scope[fld] = results[fld];
              }
           }
       }
       scope['event_status'] = (results.failed) ? 'failed' : 'success';
       });

   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl); 
   Rest.get({ params: {page_size: 1} })
       .success( function(data, status, headers, config) {
           var results = data.results[0];
           scope[form.items.event.iterator + 'NextUrl'] = data.next;
           scope[form.items.event.iterator + 'PrevUrl'] = data.previous;
           scope[form.items.event.iterator + 'Count'] = data.count;
           LoadBreadCrumbs({ path: '/jobs/' + id, title: results["summary_fields"].job.name });
           for (var fld in form.fields) {
              if (results[fld]) {
                 scope[fld] = results[fld];
              }
              if (form.fields[fld].sourceModel && results.summary_fields[form.fields[fld].sourceModel]) {
                 scope[form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField] = 
                      results.summary_fields[form.fields[fld].sourceModel][form.fields[fld].sourceField];
              }
           }
           scope[form.items.event.set] = data.results;
           SearchInit({ scope: scope, set: form.items.event.set, list: form.items.event, iterator: form.items.event.iterator, url: defaultUrl });
           PaginateInit({ scope: scope, list: form.items.event, iterator: form.items.event.iterator, url: defaultUrl , pageSize: 1 });
           scope.$emit('PostRefresh');
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to retrieve job event data: ' + $routeParams.id + '. GET status: ' + status });
           });

}

JobEvents.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobEventForm', 
                      'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'SearchInit',
                      'PaginateInit', 'GetBasePath' ];

