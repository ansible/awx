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
                           ClearScope, ProcessErrors, GetBasePath)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
    var list = JobTemplateList;
    var defaultUrl = GetBasePath('job_templates');
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var mode = (base == 'job_templates') ? 'edit' : 'select';      // if base path 'credentials', we're here to add/edit
    console.log(base);
    var scope = view.inject(list, { mode: mode });                     // Inject our view
    scope.selected = [];
  
    SearchInit({ scope: scope, set: 'job_templates', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();
    
    scope.addCredential = function() {
       $location.path($location.path() + '/add');
       }

    scope.editCredential = function(id) {
       $location.path($location.path() + '/' + id);
       }
 
    scope.deleteCredential = function(id, name) {
       
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

    scope.toggle_credential = function(idx) {
       if (scope.selected.indexOf(idx) > -1) {
          scope.selected.splice(scope.selected.indexOf(idx),1);
       }
       else {
          scope.selected.push(idx);
       }
    }
}

JobTemplatesList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobTemplateList',
                             'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
                             'ProcessErrors','GetBasePath' ];
