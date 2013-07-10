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
    
    var defaultUrl = GetBasePath('jobs') + $routeParams.id  + '/job_events/'; //?parent__isnull=1';
    
    var view = GenerateList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var scope = view.inject(list, { mode: 'edit' });
    
    $rootScope.flashMessage = null;
    scope.selected = [];
    scope.expand = true;    //on load, automatically expand all nodes

    scope.parentNode = 'parent-event';  // used in ngClass to dynamicall set row level class and control
    scope.childNode = 'child-event';    // link color and cursor

    function formatJSON(eventData) {
        //turn JSON event data into an html form
        var html = '';
        if (eventData['res']) {
           var found = false;
           var n, rows;
           if (typeof eventData.res == 'string') {
              n = eventData['res'].match(/\n/g);
              rows = (n) ? n.length : 1;
              found = true;
              html += "<label>Traceback:</label>\n";
              html += "<textarea readonly class=\"input-xxlarge\" rows=\"" + rows + "\">" + eventData.res + "</textarea>\n";
           }
           else {
              for (var fld in eventData.res) {
                  if ( (fld == 'msg' || fld == 'stdout' || fld == 'stderr') && 
                       (eventData.res[fld] !== null && eventData.res[fld] !== '') ) {
                       html += "<label>"; 
                       switch(fld) {
                          case 'msg':
                          case 'stdout':
                             html += 'Output:';
                             break;
                          case 'stderr':
                             html += 'Error:';
                             break;
                       }
                       html += "</label>\n";
                       n = eventData['res'][fld].match(/\n/g);
                       rows = (n) ? n.length : 1;
                       html += "<textarea readonly class=\"input-xxlarge\" rows=\"" + rows + "\">" + eventData.res[fld] + "</textarea>\n";
                       found = true;
                  }
                  if ( fld == "results" && Array.isArray(eventData.res[fld]) && eventData.res[fld].length > 0 ) {
                     html += "<label>Results:</label>\n";
                     //html += "<textarea readonly class="
                     var txt = '';
                     for (var i=0; i < eventData.res[fld].length; i++) {
                         txt += eventData.res[fld][i];
                     }
                     html += "<textarea readonly class=\"input-xxlarge\" rows=\"" + i + "\">" + txt + "</textarea>\n";
                     found = true;
                  }
                  if (fld == "rc" && eventData.res[fld] != 0) {
                     html += "<label>Return Code:</label>\n";
                     html += "<input type=\"text\" class=\"input-mini\" value=\"" + eventData.res[fld] + "\" readonly >\n";
                     found = true;
                  }
              }
           }
           html = (found) ? "<form class=\"event-form\">\n" + html + "</form>\n" : '';
        }
        if (eventData['host']) {
           html = "<span class=\"event-detail-host visible-phone visible-tablet\">" + eventData['host'] + "</span>\n" + html;
        }
        else {
           html = (html == '' ) ? null : html;
        }
        return html;
        }

    if (scope.RemovePostRefresh) {
       scope.RemovePostRefresh();
    }
    scope.RemovePostRefresh = scope.$on('PostRefresh', function() {
        // Initialize the parent levels
        var set = scope[list.name];
        var cDate;
        for (var i=0; i < set.length; i++) {
            set[i].event_display = set[i].event_display.replace(/^\u00a0*/g,'');
            if (set[i].event_level < 3 ) {
               set[i]['ngclick'] = "toggleChildren(" + set[i].id + ", \"" + set[i].related.children + "\")";
               set[i]['ngicon'] = 'icon-collapse-alt';
               set[i]['class'] = 'parentNode';
            }
            else {
               set[i]['class'] = 'childNode';
               set[i]['event_detail'] = formatJSON(set[i].event_data);
            }
            set[i]['show'] = true;
            set[i]['spaces'] = set[i].event_level * 24;
            if (scope.jobevents[i].failed) {
               scope.jobevents[i].status = 'error';
            }
            else if (scope.jobevents[i].changed) {
               scope.jobevents[i].status = 'changed';
            }
            else {
               scope.jobevents[i].status = 'success';
            }
            cDate = new Date(set[i].created);
            set[i].created = FormatDate(cDate);
        }
        });

    SearchInit({ scope: scope, set: 'jobevents', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });

    // Called from Inventories tab, host failed events link:
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
                        Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, GetBasePath, FormatDate) 
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
                  if (fld == 'created') {
                     var cDate = new Date(data['created']);
                     scope['created'] = FormatDate(cDate);
                  }
                  else {
                      if (data[fld]) {
                         scope[fld] = data[fld];
                      }
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
                          'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath',
                          'FormatDate'
                          ];
