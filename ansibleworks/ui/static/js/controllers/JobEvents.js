/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  JobEvents.js
 *  
 *  Controller functions for the Job Events model.
 *
 */

'use strict';

function JobEventsList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, JobEventList,
                        GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                        ClearScope, ProcessErrors, GetBasePath, LookUpInit)
{
    ClearScope('htmlTemplate');
    var list = JobEventList;
    list.base = $location.path();
    var defaultUrl = GetBasePath('jobs') + $routeParams.id + '/job_events/';
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var scope = view.inject(list, { mode: 'edit' });
    scope.selected = [];
  
    SearchInit({ scope: scope, set: 'jobevents', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();

    if (scope.PostRefreshRemove) {
       scope.PostRefreshRemove();
    }
    scope.PostRefreshRemove = scope.$on('PostRefresh', function() {
        for (var i=0; i < scope.jobevents.length; i++) {
            scope.jobevents[i].status = (scope.jobevents[i].failed) ? 'error' : 'success';
            if (scope.jobevents[i].host !== null) {
               scope.jobevents[i].host_name = scope.jobevents[i].summary_fields.host.name;
            }
        }
        });
    
    scope.editJobEvent = function(id) {
       $location.path($location.path() + '/' + id);
       }

    scope.viewHost = function(id) {
        if (id !== undefined && id !== null) {
            Rest.setUrl(GetBasePath('jobs') + $routeParams.id + '/'); 
            Rest.get()
                .success( function(data, status, headers, config) {
                    LoadBreadCrumbs({ path: '/inventories/' + data.inventory, title: data.summary_fields.inventory.name });
                    $location.path('/inventories/' + data.inventory + /hosts/ + id);
                    })
                .error( function(data, status, headers, config) {
                    ProcessErrors(scope, data, status, null,
                       { hdr: 'Error!', msg: 'Failed to lookup job record for job ' + $routeParams.id + ' GET returned status: ' + status });
                    });
            };
        }

    scope.refresh = function() {
       scope.search(list.iterator);
       }

    scope.jobDetails = function() {
       $location.path('/jobs/' + $routeParams.id);
       };

    scope.jobSummary = function() {
       $location.path('/jobs/' + $routeParams.id + '/job_host_summaries');
       };

}

JobEventsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'JobEventList',
                           'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller', 'ClearScope',
                           'ProcessErrors','GetBasePath', 'LookUpInit'
                           ];

function JobEventsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, JobEventForm, 
                        GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var form = JobEventForm;
   var generator = GenerateForm;
   var scope = GenerateForm.inject(form, {mode: 'edit', related: true});
   generator.reset();
   
   var defaultUrl = GetBasePath('base') + 'job_events/' + $routeParams.event_id + '/';
   var base = $location.path().replace(/^\//,'').split('/')[0];
   
   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl); 
   Rest.get()
       .success( function(data, status, headers, config) {
           LoadBreadCrumbs({ path: '/job_events/' + $routeParams.event_id, title: data.event });
           for (var fld in form.fields) {
               if (fld == 'status') {
                  scope['status'] = (data.failed) ? 'error' : 'success';
               }
               else if (fld == 'event_data') {
                  scope['event_data'] = JSON.stringify(data['event_data'], undefined, '\t');
               }
               else {
                  if (data[fld]) {
                     scope[fld] = data[fld];
                  }
               }
           }
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
                         { hdr: 'Error!', msg: 'Failed to retrieve event detail: ' + $routeParams.event_id + '. GET status: ' + status });
           });
   
}

JobEventsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'JobEventForm', 
                          'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath'];
