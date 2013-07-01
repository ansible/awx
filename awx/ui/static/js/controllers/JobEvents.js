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
                        ClearScope, ProcessErrors, GetBasePath, LookUpInit, ToggleChildren, EventView,
                        FormatDate)
{
    ClearScope('htmlTemplate');
    var list = JobEventList;
    list.base = $location.path();
    
    var defaultUrl = GetBasePath('jobs') + $routeParams.id  + '/job_events/?parent__isnull=1';
    
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var scope = view.inject(list, { mode: 'edit' });
    
    $rootScope.flashMessage = null;
    scope.selected = [];
    scope.expand = true;    //on load, automatically expand all nodes

    scope.parentNode = 'parent-event';  // used in ngClass to dynamicall set row level class and control
    scope.childNode = 'child-event';    // link color and cursor

    if (scope.RemovePostRefresh) {
       scope.RemovePostRefresh();
    }
    scope.RemovePostRefresh = scope.$on('PostRefresh', function() {
        // Initialize the parent levels
        var set = scope[list.name];
        var cDate;
        for (var i=0; i < set.length; i++) {
            set[i].event_display = set[i].event_display.replace(/^\u00a0*/g,'');
            if (set[i].parent == null && set[i]['ngclick'] === undefined && set[i]['ngicon'] == undefined) {
               set[i].parent = 0;
               set[i]['ngclick'] = "toggleChildren(" + set[i].id + ", \"" + set[i].related.children + "\")";
               set[i]['ngicon'] = 'icon-expand-alt';
               set[i]['level'] = 0;
               set[i]['spaces'] = 0;
               set[i]['class'] = 'parentNode';
               if (set[i]['event_data']['name']) {
                  set[i]['event_display'] = set[i]['event_data']['name'];
               }
            }
            scope.jobevents[i].status = (scope.jobevents[i].failed) ? 'error' : 'success';
            cDate = new Date(set[i].created);
            set[i].created = FormatDate(cDate);
        }

        // Expand all parent nodes
        if (scope.removeSetExpanded) {
           scope.removeSetExpanded();
        }
        scope.removeSetExpanded = scope.$on('setExpanded', function(event, latest_node) {
            // After ToggleChildren completes, look for the next parent that needs to be expanded
            var found = false; 
            var start = (latest_node) ? latest_node : 0;
            for (var i=start; i < set.length && found == false && scope.expand; i++) {
                if (set[i]['related']['children'] && (set[i]['ngicon'] == undefined || set[i]['ngicon'] == 'icon-expand-alt')) {
                   found = true;
                   ToggleChildren({
                       scope: scope, 
                       list: list, 
                       id: set[i].id,
                       children: set[i]['related']['children']
                       });
                }
            }
            if (found == false) {
               // After looping through all the nodes and finding nothing to expand, turn off 
               // auto-expand. From now on user will manually collapse and expand nodes.
               scope.expand = false;
            }
            });
        // Start the auto expansion
        set = scope[list.name];
        for (var i=0; i < set.length; i++) {
            if (set[i]['related']['children'] && (set[i]['ngicon'] == undefined || set[i]['ngicon'] == 'icon-expand-alt')) {
               ToggleChildren({
               scope: scope, 
               list: list, 
               id: set[i].id,
               children: set[i]['related']['children']
               });
            }
        }

        });

    SearchInit({ scope: scope, set: 'jobevents', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });

    // Called from Inventories tab host failed events link:
    if ($routeParams.host) {
       scope[list.iterator + 'SearchField'] = 'host'; 
       scope[list.iterator + 'SearchValue'] = $routeParams.host;
       scope[list.iterator + 'SearchFieldLabel'] = list.fields['host'].label;
    }
    
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
    
    scope.viewJobEvent = function(id) {
       EventView({"event_id": id });
       }

    scope.refresh = function() {
       scope.expand = true;
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
                           'ProcessErrors','GetBasePath', 'LookUpInit', 'ToggleChildren', 'EventView', 'FormatDate'
                           ];

function JobEventsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, JobEventForm, GenerateForm,
                        Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath) 
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
