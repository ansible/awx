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
                        ClearScope, ProcessErrors, GetBasePath, LookUpInit, ToggleChildren)
{
    ClearScope('htmlTemplate');
    var list = JobEventList;
    list.base = $location.path();
    
    var defaultUrl = GetBasePath('jobs') + $routeParams.id + '/job_events/?parent__isnull=1';
    
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var scope = view.inject(list, { mode: 'edit' });
    scope.selected = [];
  
    if (scope.RemovePostRefresh) {
       scope.RemovePostRefresh();
    }
    scope.RemovePostRefresh = scope.$on('PostRefresh', function() {
        // Initialize the parent levels
        var set = scope[list.name];
        for (var i=0; i < set.length; i++) {
            set[i].event_display = set[i].event_display.replace(/^\u00a0*/g,'');
            if (set[i].parent == null && set[i]['ngclick'] === undefined && set[i]['ngicon'] == undefined) {
               set[i].parent = 0;
               set[i]['ngclick'] = "toggleChildren(" + set[i].id + ", \"" + set[i].related.children + "\")";
               set[i]['ngicon'] = 'icon-expand-alt';
               set[i]['level'] = 0;
               set[i]['spaces'] = 0;
            }
            scope.jobevents[i].status = (scope.jobevents[i].failed) ? 'error' : 'success';
        }
        });

    SearchInit({ scope: scope, set: 'jobevents', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    scope.toggleChildren = function(id, children) {
        ToggleChildren({
            scope: scope, 
            list: list,
            id: id,
            children: children
            });
        }

    LoadBreadCrumbs();
    
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
                           'ProcessErrors','GetBasePath', 'LookUpInit', 'ToggleChildren'
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
